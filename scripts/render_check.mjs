// Captures a finished document with headless Chrome to check that boxes sit in place. Also crops the images for PR bodies.
//
//   NODE_PATH=<node_modules containing puppeteer-core> node render_check.mjs <doc.html> <out-dir> [--width 1280]
//
// Produces: <out-dir>/render.full.png (full page, with all details and all six scenario cells expanded),
//           <out-dir>/render.first.<width>.png and render.first.420.png (the first screen with nothing opened),
//           <out-dir>/render.pair<N>.png (one per screen stage .stage, side-by-side mode; also catches .pair from the old template),
//           <out-dir>/render.<dusk|bloom>.<width>.full.png (both color schemes at 1280px, default Dusk at 420px width)
// Prints one JSON line: pairs (stages found), foldedHeight (page height at the given width before anything is opened),
//   outside (stages whose boxes or numbers leave the image), overflowX (variants that scroll sideways), consoleErrors, variants, out.
// e.g. NODE_PATH=<app repo>/node_modules. The script may live outside it (createRequire).
import { createRequire } from 'node:module';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const widthAt = args.indexOf('--width');
const width = widthAt >= 0 ? Number(args.splice(widthAt, 2)[1]) : 1280;
const [doc, outDir] = args;
if (!doc || !outDir) {
  console.error('usage: node render_check.mjs <doc.html> <out-dir> [--width 1280]');
  process.exit(2);
}
const base = process.env.NODE_PATH;
if (!base) {
  console.error('Set NODE_PATH to a node_modules that contains puppeteer-core');
  process.exit(2);
}
const puppeteer = createRequire(resolve(base) + '/')('puppeteer-core');
// CHROME_PATH wins; otherwise the first Chrome or Chromium found in the usual places on macOS, Linux, and Windows
const candidates = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
];
const chrome = process.env.CHROME_PATH ?? candidates.find((p) => existsSync(p)) ?? candidates[0];
if (!existsSync(chrome)) {
  console.error(`Chrome not found: ${chrome} (set CHROME_PATH)`);
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new' });
try {
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  // Expand: open details and put each scenario in the 「여섯 단계 모두 펼치기」 (expand all six) state. Cells are not counted, so it does not depend on the number of .step
  const openAll = () => page.evaluate(() => {
    document.querySelectorAll('details').forEach((d) => { d.open = true; });
    document.querySelectorAll('.scn').forEach((s) => s.classList.add('all'));
  });
  await page.setViewport({ width, height: 1000, deviceScaleFactor: 2 });
  await page.goto(pathToFileURL(resolve(doc)).href, { waitUntil: 'load' });
  // What the reader scrolls before opening anything: the page height with every <details> closed and one scenario cell open
  const foldedHeight = await page.evaluate(() => document.documentElement.scrollHeight);
  // The first screen as the reader meets it, at both widths, before anything is opened
  await page.screenshot({ path: `${outDir}/render.first.${width}.png` });
  await page.setViewport({ width: 420, height: 1000, deviceScaleFactor: 2 });
  await page.screenshot({ path: `${outDir}/render.first.420.png` });
  await page.setViewport({ width, height: 1000, deviceScaleFactor: 2 });
  await openAll();
  await page.screenshot({ path: `${outDir}/render.full.png`, fullPage: true });
  const pairs = await page.$$('.stage, .pair');
  // The sticky table of contents would sit on top of each stage's title in these crops, so it is taken out of the way for them only
  const unstick = await page.addStyleTag({ content: 'nav.toc { position: static !important; }' });
  for (const [i, el] of pairs.entries()) {
    await el.screenshot({ path: `${outDir}/render.pair${i + 1}.png` });
  }
  await unstick.evaluate((el) => el.remove());
  // Check mechanically once whether boxes, or the numbers hung outside them, went outside the image. Whether they cover text is checked by eye
  const outside = await page.evaluate(() =>
    [...document.querySelectorAll('.shot')].flatMap((shot, s) => {
      const r = shot.getBoundingClientRect();
      return [...shot.querySelectorAll('.mark, .mark .n')]
        .map((m) => m.getBoundingClientRect())
        .filter((m) => m.left < r.left - 1 || m.top < r.top - 1 || m.right > r.right + 1 || m.bottom > r.bottom + 1)
        .map(() => s + 1);
    }),
  );
  // Looking at the layout in only one form misses things. Capture one more each for both color schemes and the narrow width. dusk is the default, with no data-theme
  const variants = [['dusk', width], ['bloom', width], ['dusk', 420]];
  const overflowX = [];
  for (const [scheme, w] of variants) {
    // The theme is set by data-theme on html, not by the system setting
    await page.evaluate((t) => { if (t === 'dusk') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t; }, scheme);
    await page.setViewport({ width: w, height: 1000, deviceScaleFactor: 2 });
    await openAll();
    await page.screenshot({ path: `${outDir}/render.${scheme}.${w}.full.png`, fullPage: true });
    // If the page scrolls horizontally at the narrow width, a table or long identifier has leaked out
    const sw = await page.evaluate(() => document.documentElement.scrollWidth);
    if (sw > w) overflowX.push(`${scheme}.${w}:${sw}`);
  }
  console.log(JSON.stringify({ pairs: pairs.length, foldedHeight, outside, overflowX, consoleErrors, variants: variants.map(([s, w]) => `${s}.${w}`), out: resolve(outDir) }));
} finally {
  await browser.close();
}
