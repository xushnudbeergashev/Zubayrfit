# Hadyaga mushuklar — loyiha pasporti

Foydalanuvchi bilan o'zbekcha (lotin) gaplashing. Javoblar juda qisqa: faqat eng muhim ma'lumot, ortiqcha gap yo'q (token tejash).
Bu fayl har bir yangi suhbat boshida o'qiladi: eski suhbat tarixi kerak emas.
**Foydalanuvchi talabi: har bir o'zgarish yoki buyruq bajarilgach, javob oxirida so'rang: «CLAUDE.md dagi holatni yangilab, commit qilaymi?» Ha desa, «Hozirgi holat» bo'limini yangilab commit + push qiling.**

GitHub repo: `xushnudbeergashev/hadyaga-mushuk` (2026-11-11 gacha nomi `Zubayrfit` edi).

Asosiy branch: `claude/admiring-ritchie-mry13c` (2026-11-11 dan default). Eski `claude/telegram-bot-uni-launch-r44ygt`
branch'ida `hadya_worker/` yo'q va token yeydigan eski `CLAUDE.md` bor: u branch'da ishlamang.

## Repoda nima bor

- `hadya_worker/`: **asosiy loyiha.** @hadyaga_mushuk_bot + Mini App, kanal @Hadyagamushuklar.
  Cloudflare Worker `https://hadyagamushuk.xushnudbeergashev.workers.dev`, D1 baza.
  Kod `src/` da, `node build.mjs` → `dist/worker.js` (panelga qo'lda joylanadi). Batafsil: `hadya_worker/README.md`.
  Testlar: `node build.mjs && node --test test/worker.test.mjs`
- `hadya_worker/marketing/`: Instagram @hadyagamushuklar (ID `17841476661325909`). Hamma ish `ig.py` orqali.
  Qoidalar va haftalik reja: `PLAYBOOK.md` (shuni o'qing).
- `hadya_worker/video/`: promo video va Reels yasash tizimi (`README.md`).
- `mushuk_bot/`: eski Python versiyasi (aiogram, SQLite). Ishlatilmaydi.
- `bot.py`, `fitness.py`: ZubayrFit fitnes bot (alohida, eski loyiha).

Adminlar: @zby_r, @xnd_e. Bot matnlari faqat o'zbek lotinida.

## Foydalanuvchi qoidalari (buzilmasin)

- Telefon raqam va Telegram username Instagram'ga hech qachon yozilmaydi (post matnini keyin o'zgartirib bo'lmaydi).
- Instagram ishlari reja bo'yicha so'ramasdan bajariladi; foydalanuvchiga faqat xato yoki muhim narsada yoziladi.
- Kunlik reja: Telegram kanaldagi e'lonlardan har kuni 1 tasi Instagram'ga post, 1 tasi story; izohlarga kuniga 1 marta javob.
- Izohlarga: bir tekshiruvda ko'pi bilan 6 ta javob, emoji va 7 kundan eski izohlarga javob yo'q.
- API «action blocked» / code 368 qaytarsa: darhol to'xtang, foydalanuvchiga ayting.
- Bio, highlight, musiqa, stiker, reklama (boost) API orqali qilinmaydi: foydalanuvchi qo'lda qiladi.
- Token va kalitlar chatga, kodga, git'ga yozilmaydi.

## Token tejash

- Katta fayllarni to'liq o'qimang (`src/index.html`, `dist/worker.js` juda katta): `grep` bilan kerakli joyni toping.
- `dist/worker.js` ni o'qimang, u `src/` dan yig'iladi.
- Jadvaldagi vazifa: «Hadyaga Instagram kunlik» (`trig_01LLwojkBVEgEtmJGRrMtPoE`), har kuni 12:47 Toshkent,
  «Hadyaga Instagram» muhitida (token o'sha yerda), har safar yangi suhbatda.

## Hozirgi holat (2026-11-11)

- Instagram 1-hafta rejasi (9–15 noyabr) `PLAYBOOK.md` da. «Uy kutayotgan 3 mushukcha» Reels 10-noyabrda yasalgan (`marketing/reels`).
  Qolgani (11-noyabr karusel, 12-noyabr «5 ta ovqat», 14-noyabr «1 daqiqada e'lon») avtomatik joylash to'xtatilgani
  sabab bajarilmaydi, foydalanuvchi so'rasa qo'lda qilinadi.
- 2026-11-11 dan kunlik vazifa yoqildi: 1 post + 1 story (`post-listing`), izohlarga kuniga 1 marta (`comments`). Birinchi ishga tushish: 12-noyabr.
