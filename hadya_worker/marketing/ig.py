#!/usr/bin/env python3
"""Hadyaga mushuklar — Instagram avtomatikasi (rasmiy Graph API).

Kalitlar kodda ham, buyruq qatorida ham yo'q: Claude Code bulut muhiti ("Hadyaga Instagram")
graph.facebook.com uchun system-user tokenini, bot manzili uchun x-marketing-key'ni o'zi qo'yadi.

Buyruqlar (hammasida --dry: hech narsa yubormasdan, nima qilinishini ko'rsatadi):
  status                      token, R2, bot holati
  comments                    izohlar va "reklama" xabarlariga javob (bir tekshiruvda <= 6 ta)
  post-listing                kanaldan bitta e'lonni Instagram post + story qilib joylash (kuniga 1 ta)
  story-given                 "Berildi"/"Sotildi" bo'lgan e'lon uchun story + postga izoh
  reel <video.mp4> <matn.txt> reels joylash (video R2'ga yuklanadi)
  carousel <matn.txt> <rasm...> karusel joylash (2-10 ta rasm)
  report                      haftalik statistika
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

G = "https://graph.facebook.com/v21.0"
IG_ID = "17841476661325909"
IG_USERNAME = "hadyagamushuklar"
BOT_HOST = "https://hadyagamushuk.xushnudbeergashev.workers.dev"
BOT_LINK = "https://t.me/hadyaga_mushuk_bot"
CHANNEL_LINK = "https://t.me/Hadyagamushuklar"
TZ = timezone(timedelta(hours=5))  # Toshkent
HERE = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry" in sys.argv
MAX_REPLIES = 6  # bir tekshiruvda ko'pi bilan shuncha javob (Meta bloklamasligi uchun)

# Izohdagi qiziqish: «hadya», «menga bering», «+», «qayerda», «nomer» kabi
INTENT = re.compile(
    r"hadya|hadiya|hadyaga|menga|bering|berasiz|beraszmi|olaman|olsam|olmoqchi|kerak|mushuk|nomer|raqam|kontakt|aloqa|"
    r"boglan|qayer|manzil|narx|qancha|necha|sotiladi|malumot|lichka|direct|direkt|"
    r"хад|менга|бер|номер|мушук|канча|қанча|керак|олам", re.I)
PLUS_ONLY = re.compile(r"^\s*\+{1,3}\s*$")


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- HTTP
def http(method, url, data=None, headers=None, raw=None, timeout=120):
    h = {"user-agent": "hadyaga-marketing/1.0", **(headers or {})}  # Cloudflare urllib'ning standart nomini bloklaydi (1010)
    body = None
    if raw is not None:
        body = raw
    elif data is not None:
        if h.get("content-type") == "application/json":
            body = json.dumps(data).encode()
        else:
            body = urllib.parse.urlencode(data).encode()
            h.setdefault("content-type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode()
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
    try:
        return json.loads(txt)
    except ValueError:
        return {"raw": txt}


def gget(path, **params):
    return http("GET", f"{G}/{path}?{urllib.parse.urlencode(params)}")


def gpost(path, **data):
    return http("POST", f"{G}/{path}", data)


def gpost_json(path, payload):
    return http("POST", f"{G}/{path}", payload, {"content-type": "application/json"})


# Bot serveri: kalitni proksi qo'yadi (sarlavha bo'lishi kerak, qiymati almashtiriladi)
MK = {"x-marketing-key": "proxy-injected"}


def mk_get(path, **params):
    return http("GET", f"{BOT_HOST}{path}?{urllib.parse.urlencode(params)}", headers=MK)


def mk_state():
    return mk_get("/mk/state", prefix="ig").get("items", {})


def mk_set(key, value):
    if DRY:
        log(f"  [dry] holat {key} = {value}")
        return
    http("POST", f"{BOT_HOST}/mk/state", {"key": key, "value": value}, {**MK, "content-type": "application/json"})


def mk_upload(path, name):
    if DRY:
        return f"{BOT_HOST}/media/{name}"
    ext = name.rsplit(".", 1)[-1]
    ctype = {"mp4": "video/mp4", "jpg": "image/jpeg", "png": "image/png"}.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        r = http("PUT", f"{BOT_HOST}/mk/media/{name}", raw=f.read(), headers={**MK, "content-type": ctype}, timeout=300)
    if not r.get("ok"):
        raise RuntimeError(f"R2'ga yuklanmadi: {r}")
    return r["url"]


def all_listings():
    items, since = [], 0
    while True:
        r = mk_get("/mk/listings", since=since, limit=100)
        page = r.get("items", [])
        items += page
        if len(page) < 100:
            return items
        since = page[-1]["id"]


# ---------------------------------------------------------------- media tayyorlash (ffmpeg)
# Instagram lentasi 4:5 dan tik rasmni qabul qilmaydi: hammasi 1080x1350 ga, fon xira qilib keltiriladi
def fit_filter(w, h):
    return (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=28:4,eq=brightness=-0.06[bg];"
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


def download(url, path):
    req = urllib.request.Request(url, headers={"user-agent": "hadyaga-marketing/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def prep_image(src, dst, w=1080, h=1350):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", fit_filter(w, h),
                    "-frames:v", "1", "-q:v", "3", dst], check=True)


def has_audio(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", src],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def prep_video(src, dst, w=1080, h=1350):
    audio = has_audio(src)
    args = ["ffmpeg", "-loglevel", "error", "-y", "-i", src]
    if not audio:  # Instagram ovozsiz videoni ba'zan rad etadi — jim ovoz qo'shiladi
        args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    args += ["-filter_complex", fit_filter(w, h) + "[v]", "-map", "[v]", "-map", "0:a:0" if audio else "1:a:0",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-t", "59", "-shortest", "-movflags", "+faststart", dst]
    subprocess.run(args, check=True)


# ---------------------------------------------------------------- joylash
def wait_ready(cid, tries=40):
    for _ in range(tries):
        st = gget(cid, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return True
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram faylni qabul qilmadi: {gget(cid, fields='status_code,status')}")
        time.sleep(6)
    raise RuntimeError("Instagram faylni juda uzoq tayyorladi")


def container(**params):
    if DRY:
        log("  [dry] konteyner:", {k: (v[:60] + "…" if isinstance(v, str) and len(v) > 60 else v) for k, v in params.items()})
        return "DRY"
    r = gpost(f"{IG_ID}/media", **params)
    if "id" not in r:
        raise RuntimeError(f"Konteyner yaratilmadi: {r}")
    return r["id"]


def publish(cid):
    if DRY:
        return "DRY_MEDIA"
    wait_ready(cid)
    r = gpost(f"{IG_ID}/media_publish", creation_id=cid)
    if "id" not in r:
        raise RuntimeError(f"Joylanmadi: {r}")
    return r["id"]


def publish_feed(items, caption):
    """items: [(type, public_url)]; 1 ta rasm → IMAGE, 1 ta video → REELS, ko'p → CAROUSEL"""
    if len(items) == 1:
        t, url = items[0]
        if t == "photo":
            return publish(container(image_url=url, caption=caption))
        return publish(container(media_type="REELS", video_url=url, caption=caption, share_to_feed="true"))
    kids = []
    for t, url in items[:10]:
        kid = container(image_url=url, is_carousel_item="true") if t == "photo" else \
            container(media_type="VIDEO", video_url=url, is_carousel_item="true")
        if not DRY:
            wait_ready(kid)
        kids.append(kid)
    return publish(container(media_type="CAROUSEL", children=",".join(kids), caption=caption))


def publish_story(image_url):
    return publish(container(media_type="STORIES", image_url=image_url))


# ---------------------------------------------------------------- matn (A variant: kontaktlarsiz)
CONTACT_LINE = re.compile(r"📞|☎|🌎|✈️|telefon|\btel\b|telegram|t\.me/|@\w|e'lon berish uchun|kanal:", re.I)


def ig_caption(it):
    lines = []
    for ln in it["caption"].split("\n"):
        digits = re.sub(r"\D", "", ln)
        if CONTACT_LINE.search(ln) or (len(digits) >= 9 and not re.search(r"narx|so.?m|sum|\$", ln, re.I)):
            continue
        lines.append(ln.rstrip())
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    text = re.sub(r"(^|[^\w/])@([A-Za-z]\w{3,31})", r"\1t.me/\2", text)  # Telegram @ism Instagram'da boshqa akkaunt bo'lib qolmasin
    word = {"hadya": "hadya", "sotuv": "mushuk"}.get(it["kind"], "ma'lumot")
    tags = ["#mushuk", "#mushukcha", "#mushuklar", "#hadyagamushuk", "#cat", "#kitten", "#uzbekistan"]
    if "Toshkent" in (it.get("region") or ""):
        tags.append("#toshkent")
    text += (f"\n\n📩 Egasi bilan bog'lanish: izohga «{word}» deb yozing — Direct'ga e'lon havolasini yuboramiz."
             f"\n\n🤖 E'lon berish: t.me/hadyaga_mushuk_bot\n📢 Telegram kanal: t.me/Hadyagamushuklar\n\n" + " ".join(tags))
    return text[:2150]


def norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return re.sub(r"[^a-zа-яё0-9]+", "", re.sub(r"#\w+", "", t))


def match_listing(caption, listings):
    """Qo'lda joylangan eski postlar uchun: matni o'xshash kanal e'lonini topadi"""
    key = norm(caption)[:220]
    if len(key) < 40:
        return None
    best, score = None, 0
    for it in listings:
        s = difflib.SequenceMatcher(None, key, norm(it["caption"])[:220]).ratio()
        if s > score:
            best, score = it, s
    return best if score >= 0.82 else None


# ---------------------------------------------------------------- buyruqlar
def cmd_status():
    log("token:", gget("me", fields="id,name"))
    log("instagram:", gget(IG_ID, fields="username,followers_count,media_count"))
    log("bot:", mk_get("/mk/status"))


def dm_text(it):
    if it and it["status"] == "published" and it.get("channel_url"):
        return (f"Assalomu alaykum! 🐾 Siz so'ragan mushuk e'loni Telegram kanalimizda — egasining kontaktlari shu yerda:\n"
                f"{it['channel_url']}\n\nBoshqa mushuklarni hududingiz bo'yicha botimizdan qidirishingiz mumkin.\n\n{BOT_LINK}")
    if it and it["status"] in ("given", "sold", "closed"):
        return (f"Assalomu alaykum! Afsuski, bu mushuk allaqachon yangi uyini topdi 🏠\n"
                f"Hadyaga va sotuvdagi boshqa mushuklar Telegram kanalimizda: {CHANNEL_LINK}\n\n{BOT_LINK}")
    return (f"Assalomu alaykum! 🐾 Hadyaga va sotuvdagi mushuklar Telegram kanalimizda: {CHANNEL_LINK}\n"
            f"Botimizda hududingiz bo'yicha mushuk topasiz yoki o'zingiz e'lon berasiz.\n\n{BOT_LINK}")


def cmd_comments():
    state = mk_state()
    listings = {it["id"]: it for it in all_listings()}
    price = mk_get("/mk/status").get("price_text", "")
    now = datetime.now(timezone.utc)
    sent = 0
    media = gget(f"{IG_ID}/media", fields="id,caption,timestamp", limit=30).get("data", [])
    for m in media:
        if sent >= MAX_REPLIES:
            break
        lid = state.get(f"igm:{m['id']}")
        it = listings.get(int(lid)) if lid else None
        if not it:
            it = match_listing(m.get("caption"), list(listings.values()))
        comments = gget(f"{m['id']}/comments", fields="id,text,username,timestamp", limit=50).get("data", [])
        for c in comments:
            if sent >= MAX_REPLIES:
                break
            key = f"igc:{c['id']}"
            if state.get(key) or c.get("username") == IG_USERNAME:
                continue
            age = now - datetime.fromisoformat(c["timestamp"].replace("+0000", "+00:00"))
            text = c.get("text") or ""
            letters = re.sub(r"[\W\d_]+", "", text)
            if age > timedelta(days=7) or (not letters and not PLUS_ONLY.match(text)) or \
                    not (INTENT.search(text) or PLUS_ONLY.match(text)):
                mk_set(key, "skip")  # eski, faqat emoji yoki qiziqish bildirmagan izoh — javobsiz
                continue
            msg = dm_text(it)
            log(f"izoh @{c.get('username')}: {text[:60]!r} → Direct ({'e`lon #' + str(it['id']) if it else 'kanal'})")
            if not DRY:
                r1 = gpost_json(f"{IG_ID}/messages", {"recipient": {"comment_id": c["id"]}, "message": {"text": msg}})
                ok = "message_id" in r1 or "recipient_id" in r1
                if ok:
                    gpost(f"{c['id']}/replies", message=f"@{c.get('username')} Direct'ga xabar yubordik 📩")
                else:
                    log("  Direct yuborilmadi:", r1)
            mk_set(key, "dm")
            sent += 1

    # Direct'da «reklama» deb yozganlar (oxirgi 24 soat)
    conv = gget(f"{IG_ID}/conversations", platform="instagram",
                fields="messages.limit(3){id,message,from,created_time}", limit=20).get("data", [])
    for cv in conv:
        if sent >= MAX_REPLIES:
            break
        for msg in cv.get("messages", {}).get("data", []):
            frm = msg.get("from", {})
            if frm.get("id") == IG_ID or frm.get("username") == IG_USERNAME:
                break  # oxirgi xabar bizniki — javob berilgan
            key = f"igdm:{msg['id']}"
            created = datetime.fromisoformat(msg["created_time"].replace("+0000", "+00:00"))
            if state.get(key) or now - created > timedelta(hours=23) or not re.search(r"reklama|реклама", msg.get("message") or "", re.I):
                continue
            text = (f"Assalomu alaykum! Reklama joylash uchun botimizga kiring → «E'lon» → «Reklama». "
                    f"Narxi: {price}, admin ma'qullagandan keyin to'lanadi.\n\n{BOT_LINK}")
            log(f"Direct @{frm.get('username')}: {msg.get('message','')[:40]!r} → reklama javobi")
            if not DRY:
                r = gpost_json(f"{IG_ID}/messages", {"recipient": {"id": frm["id"]}, "message": {"text": text}})
                if "message_id" not in r:
                    log("  yuborilmadi:", r)
            mk_set(key, "dm")
            sent += 1
            break
    log(f"Javoblar: {sent}")


def story_image(mode, it, photo_path):
    with tempfile.TemporaryDirectory() as td:
        sj = os.path.join(td, "s.json")
        png = os.path.join(td, "s.png")
        jpg = os.path.join(td, "s.jpg")
        json.dump({"mode": mode, "photo": photo_path, "kind": it["kind"], "title": it["title"],
                   "place": f"{it['region']}, {it['district']}", "price": it.get("price")}, open(sj, "w"))
        subprocess.run(["node", os.path.join(HERE, "story.mjs"), sj, png], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", png, "-q:v", "2", jpg], check=True)
        return mk_upload(jpg, f"story-{mode}-{it['id']}-{int(time.time())}.jpg")


def cmd_post_listing():
    state = mk_state()
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    if state.get(f"igday:{today}") and "--force" not in sys.argv:
        log("Bugun kanaldan e'lon allaqachon joylangan.")
        return
    now = time.time()
    cands = [it for it in all_listings() if it["status"] == "published" and not it["no_ig"] and it["media"]
             and not state.get(f"ig:L{it['id']}")]
    fresh = sorted([it for it in cands if not it["imported"] and now - (it["published_at"] or 0) < 30 * 86400], key=lambda x: -x["id"])
    old = sorted([it for it in cands if it["imported"] and now - (it["published_at"] or 0) < 14 * 86400], key=lambda x: -x["id"])
    pick = (fresh or old or [None])[0]
    if not pick:
        log("Joylanadigan e'lon yo'q.")
        return
    log(f"E'lon #{pick['id']} ({pick['kind']}, {pick['title']}) → Instagram")
    caption = ig_caption(pick)
    log("--- matn ---\n" + caption + "\n------------")
    with tempfile.TemporaryDirectory() as td:
        items, first_photo = [], None
        for i, m in enumerate(pick["media"][:10]):
            src = os.path.join(td, f"src{i}")
            download(m["url"], src)
            if m["type"] == "video":
                dst = os.path.join(td, f"v{i}.mp4")
                single = len(pick["media"]) == 1
                prep_video(src, dst, 1080, 1920 if single else 1350)
                items.append(("video", mk_upload(dst, f"l{pick['id']}-{i}-{int(now)}.mp4")))
            else:
                dst = os.path.join(td, f"p{i}.jpg")
                prep_image(src, dst)
                first_photo = first_photo or src
                items.append(("photo", mk_upload(dst, f"l{pick['id']}-{i}-{int(now)}.jpg")))
        media_id = publish_feed(items, caption)
        log("Post joylandi:", media_id)
        mk_set(f"ig:L{pick['id']}", media_id)
        mk_set(f"igm:{media_id}", pick["id"])
        mk_set(f"igday:{today}", pick["id"])
        if first_photo:
            sid = publish_story(story_image("new", pick, first_photo))
            log("Story joylandi:", sid)


def cmd_story_given():
    state = mk_state()
    now = time.time()
    cands = [it for it in all_listings() if it["status"] in ("given", "sold") and it["media"] and not state.get(f"iggiven:L{it['id']}")
             and now - (it["closed_at"] or 0) < 3 * 86400 and any(m["type"] == "photo" for m in it["media"])]
    cands.sort(key=lambda x: (not state.get(f"ig:L{x['id']}"), -x["id"]))  # Instagram'da posti borlar birinchi
    if not cands:
        log("Yangi berilgan e'lon yo'q.")
        return
    it = cands[0]
    mode = "sold" if it["status"] == "sold" else "given"
    log(f"E'lon #{it['id']} → «{mode}» story")
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "p")
        download(next(m["url"] for m in it["media"] if m["type"] == "photo"), src)
        sid = publish_story(story_image(mode, it, src))
        log("Story joylandi:", sid)
    post = state.get(f"ig:L{it['id']}")
    if post and not DRY:
        word = "Sotildi" if mode == "sold" else "Berildi"
        gpost(f"{post}/comments", message=f"✅ {word} — bu mushuk yangi uyini topdi 🏠 Rahmat!")
    mk_set(f"iggiven:L{it['id']}", "1")


def cmd_reel(video, caption_file):
    caption = open(caption_file, encoding="utf-8").read().strip()
    url = mk_upload(video, f"reel-{int(time.time())}.mp4")
    log("Reels joylandi:", publish(container(media_type="REELS", video_url=url, caption=caption, share_to_feed="true")))


def cmd_carousel(caption_file, images):
    caption = open(caption_file, encoding="utf-8").read().strip()
    urls = [("photo", mk_upload(p, f"car-{int(time.time())}-{i}.jpg")) for i, p in enumerate(images)]
    log("Karusel joylandi:", publish_feed(urls, caption))


def cmd_report():
    until = int(time.time())
    since = until - 7 * 86400
    acc = gget(f"{IG_ID}/insights", metric="reach,views,profile_views,accounts_engaged,total_interactions,website_clicks",
               period="day", metric_type="total_value", since=since, until=until)
    log("7 kun:", {d["name"]: d.get("total_value", {}).get("value") for d in acc.get("data", [])} or acc)
    log("instagram:", gget(IG_ID, fields="followers_count,media_count"))
    for m in gget(f"{IG_ID}/media", fields="id,timestamp,media_product_type,caption,like_count,comments_count", limit=15).get("data", []):
        if datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).timestamp() < since:
            continue
        mt = "reach,views,saved,shares" + (",ig_reels_avg_watch_time" if m["media_product_type"] == "REELS" else "")
        ins = {d["name"]: d["values"][0]["value"] for d in gget(f"{m['id']}/insights", metric=mt).get("data", [])}
        log(m["timestamp"][:10], m["media_product_type"], ins, "like", m.get("like_count"), "izoh", m.get("comments_count"),
            (m.get("caption") or "")[:40].replace("\n", " "))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    cmd, rest = args[0], args[1:]
    {"status": cmd_status, "comments": cmd_comments, "post-listing": cmd_post_listing, "story-given": cmd_story_given,
     "report": cmd_report, "reel": lambda: cmd_reel(*rest), "carousel": lambda: cmd_carousel(rest[0], rest[1:])}[cmd]()
