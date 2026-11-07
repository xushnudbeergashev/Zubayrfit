// Story rasmi (1080×1920 PNG) yasaydi: node story.mjs <story.json> <chiqish.png>
// story.json: {mode: "new"|"given"|"sold", photo: "<rasm yo'li yoki URL>", kind, title, place, price}
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "/opt/node-tools/node_modules/playwright/index.mjs";

const dir = path.dirname(fileURLToPath(import.meta.url));
const [, , inFile, outFile] = process.argv;
const s = JSON.parse(fs.readFileSync(inFile, "utf8"));
if (s.photo && !/^https?:|^data:/.test(s.photo)) s.photo = pathToFileURL(path.resolve(s.photo)).href;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto(pathToFileURL(path.join(dir, "story.html")).href);
await p.evaluate((s) => window.fill(s), s);
await p.evaluate(() => document.fonts.ready);
await p.waitForFunction(() => { const i = new Image(); i.src = getComputedStyle(document.getElementById("ph")).backgroundImage.slice(5, -2); return i.decode().then(() => true, () => true); });
await p.waitForTimeout(300);
await p.screenshot({ path: outFile });
await b.close();
