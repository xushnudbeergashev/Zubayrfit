# Hadyaga mushuklar — Instagram ish tartibi

Akkaunt: **@hadyagamushuklar** (ID `17841476661325909`). Faqat rasmiy Graph API ishlatiladi: Meta ilovasi
«Hadyaga mushuklar», system-user tokeni Claude Code bulut muhitida («Hadyaga Instagram») saqlanadi.
Token va kalitlar hech qachon chatga, kodga yoki git'ga yozilmaydi.

Bot serveri: `https://hadyagamushuk.xushnudbeergashev.workers.dev`
- `/mk/*`: `x-marketing-key` sarlavhasi bilan (qiymati botdagi `SETUP_KEY`, proksi o'zi qo'yadi);
- `/media/<nom>`: R2'dagi faylning ochiq havolasi.

Barcha ishlar `ig.py` orqali bajariladi (`python3 ig.py <buyruq> [--dry]`).

## Jadval (Toshkent vaqti)

| Vaqt | Ish | Buyruq |
|---|---|---|
| 12:47 (kunlik vazifa) | Kanaldan 1 ta e'lon: post + story, keyin izohlarga javob (kuniga 1 marta) | `python3 ig.py post-listing`, `python3 ig.py comments` |
| 19:00 | Haftalik rejadagi kontent, keyin «Berildi» story | reja bo'yicha + `python3 ig.py story-given` |
| Yakshanba 19:00 | Haftalik hisobot (jadval ko'rinishida) va keyingi hafta rejasi | `python3 ig.py report` |

## Qoidalar

**Mustaqillik** (foydalanuvchi 2026-11-07 da aytgan): reja bo'yicha hammasi so'ramasdan bajariladi, har kuni tasdiq
so'ralmaydi. Foydalanuvchiga faqat xato yoki muhim narsada yoziladi, har yakshanba esa jadval ko'rinishida hisobot
beriladi. Telefon raqam va Telegram username Instagram'ga hech qachon yozilmaydi.

**Izohlar**
- Qiziqish bildirgan izohlarga («hadya», «menga bering», «+», «qayerda», «nomer», «mushuk»…) Direct'ga **bitta** xabar
  (Private Reply), ochiq javob esa «Direct'ga xabar yubordik 📩».
- Direct'da **aynan o'sha postdagi e'lonning Telegram havolasi** beriladi. Mushuk berilgan bo'lsa, «allaqachon uy topdi»
  va kanal havolasi. Bot havolasi har doim matndan keyin, alohida oxirgi qatorda.
- Emoji, eski (7 kundan ortiq) va qiziqish bildirmagan izohlarga javob yo'q.
- Bitta tekshiruvda ko'pi bilan 6 ta javob.

**Direct**: «reklama» deb yozganlarga reklama joylash tartibi va narxi (narx botdan olinadi).

**Kanaldan e'lonlar (A variant)**
- Instagram matnida telefon va Telegram username **yo'q**. Instagram post matnini keyin o'zgartirib bo'lmaydi,
  kontakt esa abadiy qolib ketardi. O'rniga: «izohga «hadya» deb yozing — Direct'ga e'lon havolasini yuboramiz».
- Telegram @ism Instagram'da boshqa akkauntga havola bo'lib qolmasligi uchun `t.me/ism` ko'rinishida yoziladi.
- Kuniga 1 ta. Avval bot orqali berilgan yangi e'lonlar (30 kun ichidagi), keyin kanaldan import qilinganlar (14 kun).
- Egasi «Instagram'ga ham joylansin» belgisini olib tashlagan bo'lsa (`no_ig`), joylanmaydi.
- Rasm va videolar 1080×1350 ga xira fon bilan keltiriladi (lenta 4:5 dan tik rasmni qabul qilmaydi).

**«Berildi» / «Sotildi»**: yashil «✅ Yangi uyini topdi!» story. Instagram'da posti bo'lsa, ostiga «✅ Berildi» izohi.

**Xavfsizlik**
- Yangi ilova: birinchi haftalarda sekin ishlanadi, limitlar oshirilmaydi.
- API «action blocked», «temporarily blocked», `code 368` yoki shaxsni tasdiqlash so'rasa, **darhol to'xtash** va
  foydalanuvchiga yozish.
- Bio, highlight, musiqa, stiker va reklama (boost) API orqali qilinmaydi: ularni foydalanuvchi qo'lda qiladi.

## 1-hafta rejasi (9–15 noyabr 2026) — tasdiqlangan

| Kun | 19:00 kontent |
|---|---|
| Du 9 | 🎬 Reels «Uy kutayotgan 3 mushukcha», 10–12 s: kanaldagi faol hadya e'lonlaridan 3 ta rasm, har birida zot/yosh/hudud, oxirida «Telegram: @hadyaga_mushuk_bot» |
| Se 10 | 🎬 Dushanbadan ko'chirildi: Reels «Uy kutayotgan 3 mushukcha» (9-noyabr ishchi jarayon qayta ishga tushgani sabab o'tib ketgan) |
| Ch 11 | 📸 Karusel «Kanal orqali N ta mushuk uy topdi» (N: ilova statistikasidagi «berildi» soni), 4 slayd: raqam → 3 ta berilgan mushuk → «Siz ham e'lon bering» |
| Pa 12 | 🎬 Reels «Mushukchaga mumkin bo'lmagan 5 ta ovqat», 12–15 s: shokolad, piyoz/sarimsoq, uzum/mayiz, sigir suti, suyak; oxirida bot |
| Ju 13 | — (faqat story-given) |
| Sh 14 | 🎬 Reels «1 daqiqada e'lon berish», 10 s: ilova ekranlari (rasm tanlash → forma → yuborish), oxirida bot |
| Ya 15 | 📝 `ig.py report`: jadval ko'rinishidagi hisobot va 2-hafta rejasi (shu faylga qo'shiladi, keyin bajariladi) |

Reels: 1080×1920, birinchi soniyada savol yoki mushuk yuzi (o'rtacha tomosha vaqti hozir ~7 s), ovozsiz ham
tushunarli yozuvlar, musiqa `video/make-music.py` bilan. Yig'ish: `video/` dagi sahna/render tizimi.
Matn oxirida: «Mushukingizga uy kerakmi? 👉 Telegram: t.me/hadyaga_mushuk_bot» va 8–10 hashtag.
