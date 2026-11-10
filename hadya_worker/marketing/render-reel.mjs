// Reels sahnasini (window.render(t), window.DURATION, window.SCENE_STARTS) MP4 ga aylantiradi, mayin musiqa bilan.
// Ishlatish: node render-reel.mjs <sahna.html> <data.json> <chiqish.mp4> [--stills 1,5,9]
// data.json sahnaga window.CATS (yoki window.DATA) sifatida beriladi.
import fs from "node:fs";
import path from "node:path";
import { spawn, execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "/opt/node-tools/node_modules/playwright/index.mjs";

const dir = path.dirname(fileURLToPath(import.meta.url));
const [, , stage, dataFile, outFile] = process.argv;
const si = process.argv.indexOf("--stills");
const FPS = 30;
const data = JSON.parse(fs.readFileSync(dataFile, "utf8"));
for (const c of Array.isArray(data) ? data : []) if (c.photo && !/^(https?|data|file):/.test(c.photo)) c.photo = pathToFileURL(path.resolve(c.photo)).href;

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
p.on("pageerror", (e) => console.log("[xato]", e.message));
await p.addInitScript((d) => { window.CATS = d; window.DATA = d; }, data);
await p.goto(pathToFileURL(path.resolve(stage)).href);
await p.evaluate(() => document.fonts.ready);
await p.evaluate((d) => Promise.all(d.filter((c) => c.photo).map((c) => { const i = new Image(); i.src = c.photo; return i.decode().catch(() => {}); })), Array.isArray(data) ? data : []);
const LEN = await p.evaluate(() => window.DURATION);

if (si > 0) {
  for (const t of process.argv[si + 1].split(",").map(Number)) {
    await p.evaluate((t) => window.render(t), t);
    await p.screenshot({ path: outFile.replace(/\.mp4$/, `-${t}.jpg`), type: "jpeg", quality: 85 });
  }
  await b.close();
  process.exit(0);
}

const music = outFile.replace(/\.mp4$/, ".wav");
execFileSync("python3", [path.join(dir, "../video/make-music.py"), String(LEN), music,
  JSON.stringify(await p.evaluate(() => window.SCENE_STARTS)), "soft"], { stdio: "inherit" });
const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-", "-i", music,
  "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-r", String(FPS),
  "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", outFile],
  { stdio: ["pipe", "inherit", "inherit"] });
for (let f = 0; f < LEN * FPS; f++) {
  await p.evaluate((t) => window.render(t), f / FPS);
  const buf = await p.screenshot({ type: "jpeg", quality: 93 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await b.close();
fs.rmSync(music, { force: true });
console.log("Tayyor:", outFile);
