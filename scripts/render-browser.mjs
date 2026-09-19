#!/usr/bin/env node
/**
 * render-browser.mjs — self-contained fallback renderer for knowledge-motion
 * compositions. Drives a local Chrome/Edge/Chromium via puppeteer-core,
 * steps the GSAP timelines frame by frame (seek runtime injected from here,
 * never baked into the composition), captures JPEG frames, and encodes an
 * MP4 with ffmpeg. No hyperframes CLI required.
 *
 * Usage:
 *   node scripts/render-browser.mjs <composition.html> [--fps 30] [--output renders/output.mp4] [--quality 80]
 *
 * Environment:
 *   KMV_CHROME  absolute path to the browser binary to use (takes priority).
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));

// ---------- CLI args ----------
function parseArgs(argv) {
  const args = {
    input: null,
    fps: 30,
    output: "renders/output.mp4",
    quality: 80,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--fps") args.fps = Number(argv[++i]);
    else if (a === "--output") args.output = argv[++i];
    else if (a === "--quality") args.quality = Number(argv[++i]);
    else if (!a.startsWith("--")) args.input = a;
    else {
      console.error(`Unknown option: ${a}`);
      process.exit(2);
    }
  }
  if (!args.input) {
    console.error("Usage: node render-browser.mjs <composition.html> [--fps N] [--output path.mp4] [--quality N]");
    process.exit(2);
  }
  if (!Number.isFinite(args.fps) || args.fps <= 0) {
    console.error(`Invalid --fps: ${args.fps}`);
    process.exit(2);
  }
  if (!Number.isFinite(args.quality) || args.quality < 1 || args.quality > 100) {
    console.error(`Invalid --quality: ${args.quality}`);
    process.exit(2);
  }
  return args;
}

// ---------- browser detection ----------
function findChromeBinary() {
  const candidates = [];
  if (process.env.KMV_CHROME) candidates.push(process.env.KMV_CHROME);
  candidates.push(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  );
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  // last resort: whatever chromium is on PATH
  const which = spawn("which", ["chromium"], { stdio: ["ignore", "pipe", "ignore"] });
  const found = new Promise((resolve) => {
    let out = "";
    which.stdout.on("data", (d) => (out += d));
    which.on("close", (code) => resolve(code === 0 ? out.trim() : null));
  });
  return found;
}

// ---------- seek runtime (injected, not part of the composition) ----------
// Steps every clip and every registered GSAP timeline to an absolute time.
// Passed to page.evaluate as a real function so frame time and duration are
// forwarded as arguments. Note: CSS transitions could fight per-frame seeks
// (a transition started at frame N would still be interpolating at frame N+1
// regardless of the seeked inline styles). The compositions rendered here do
// not use CSS transitions, so we do not force transitions off; if one ever
// sneaks in, inject `*{transition:none!important}` here.
async function seekRuntime(t, rootDuration) {
  const root = document.getElementById('root');
  if (!root) throw new Error('no #root element');
  // 1) clip visibility from data-start / data-duration
  for (const clip of root.querySelectorAll('.clip')) {
    const start = parseFloat(clip.dataset.start || '0');
    const dur = clip.dataset.duration !== undefined
      ? parseFloat(clip.dataset.duration)
      : rootDuration;
    const visible = t >= start && t < start + dur;
    clip.style.visibility = visible ? 'visible' : 'hidden';
    clip.style.pointerEvents = visible ? 'auto' : 'none';
  }
  // 2) seek every registered GSAP timeline to the absolute frame time.
  //    seek() force-renders the timeline at t, so paused timelines still
  //    update inline styles.
  const tls = window.__timelines || {};
  for (const key of Object.keys(tls)) {
    const tl = tls[key];
    if (tl && typeof tl.seek === 'function') tl.seek(t, false);
  }
  return Object.keys(tls).length;
}

function runFfmpeg(framesDir, fps, output) {
  return new Promise((resolve, reject) => {
    const ff = spawn(
      "ffmpeg",
      [
        "-y",
        "-framerate", String(fps),
        "-i", path.join(framesDir, "frame_%06d.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output,
      ],
      { stdio: ["ignore", "ignore", "pipe"] },
    );
    let err = "";
    ff.stderr.on("data", (d) => (err += d));
    ff.on("error", reject);
    ff.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited with code ${code}:\n${err.split("\n").slice(-8).join("\n")}`));
    });
  });
}

// ---------- main ----------
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = path.resolve(args.input);
  if (!fs.existsSync(inputPath)) {
    console.error(`Composition not found: ${inputPath}`);
    process.exit(2);
  }
  const outputPath = path.resolve(args.output);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const log = (msg) => process.stderr.write(`[render] ${msg}\n`);

  log("locating browser...");
  const binaryPath = await findChromeBinary();
  if (!binaryPath) {
    console.error("No browser found. Set KMV_CHROME to a Chrome/Edge/Chromium binary path.");
    process.exit(3);
  }
  log(`browser: ${binaryPath}`);

  const framesDir = fs.mkdtempSync(path.join(os.tmpdir(), "kmv-frames-"));
  const browser = await puppeteer.launch({
    executablePath: binaryPath,
    headless: true,
    args: ["--no-first-run", "--disable-extensions", "--hide-scrollbars", "--force-device-scale-factor=1"],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
    // Local/vendor scripts only: the composition contract forbids render-time
    // network, so a plain domcontentloaded wait is sufficient and resilient.
    await page.goto("file://" + inputPath, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.evaluate(async () => {
      await document.fonts.ready;
      // wait for the composition to register its GSAP timelines
      const deadline = Date.now() + 10000;
      while ((!window.__timelines || Object.keys(window.__timelines).length === 0) && Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 50));
      }
      // settle pending image/layout work
      const imgs = Array.from(document.images);
      await Promise.all(imgs.map((img) => img.complete ? null : new Promise((r) => { img.onload = img.onerror = r; })));
    });

    const meta = await page.evaluate(() => {
      const root = document.getElementById("root");
      if (!root) throw new Error("composition has no #root element");
      return {
        width: parseInt(root.dataset.width || root.style.width, 10),
        height: parseInt(root.dataset.height || root.style.height, 10),
        duration: parseFloat(root.dataset.duration || "0"),
      };
    });
    if (!meta.width || !meta.height || !meta.duration) {
      throw new Error(`bad composition metadata on #root: ${JSON.stringify(meta)}`);
    }
    const totalFrames = Math.round(meta.duration * args.fps);
    log(`composition: ${meta.width}x${meta.height}, ${meta.duration}s @ ${args.fps}fps = ${totalFrames} frames`);
    log(`timelines registered: ${await page.evaluate(() => Object.keys(window.__timelines || {}).length)}`);

    await page.setViewport({ width: meta.width, height: meta.height, deviceScaleFactor: 1 });

    for (let i = 0; i < totalFrames; i++) {
      const t = i / args.fps;
      const registered = await page.evaluate(seekRuntime, t, meta.duration);
      if (registered === 0) throw new Error('no timelines registered on window.__timelines');
      await page.screenshot({
        path: path.join(framesDir, `frame_${String(i + 1).padStart(6, "0")}.jpg`),
        type: "jpeg",
        quality: args.quality,
        clip: { x: 0, y: 0, width: meta.width, height: meta.height },
      });
      if ((i + 1) % 30 === 0 || i === totalFrames - 1) {
        log(`frame ${i + 1}/${totalFrames} (t=${t.toFixed(3)}s)`);
      }
    }

    log("encoding mp4 with ffmpeg...");
    await runFfmpeg(framesDir, args.fps, outputPath);
    log(`done: ${outputPath}`);
  } finally {
    await browser.close().catch(() => {});
    fs.rmSync(framesDir, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(`[render] FAILED: ${err && err.stack ? err.stack : err}`);
  process.exit(1);
});
