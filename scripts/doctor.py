#!/usr/bin/env python3
"""Environment doctor for the knowledge-motion pipeline.

Checks python3, node, ffmpeg, ffprobe, a Chrome binary, the hyperframes CLI
(via npx, 20s timeout) and coli. Prints a human-readable table plus fix
suggestions; ``--json`` emits the raw report instead.

Exit code is 0 when the core tools (ffmpeg + ffprobe) are available,
1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)

SUGGESTIONS = {
    "python3": "Install Python 3.9+ (e.g. `brew install python`).",
    "node": "Install Node.js 18+ (https://nodejs.org or `brew install node`).",
    "ffmpeg": "Install FFmpeg (e.g. `brew install ffmpeg`). Required for mixing and verification.",
    "ffprobe": "Install FFmpeg (e.g. `brew install ffmpeg`). ffprobe ships with it.",
    "chrome": "Install Google Chrome, or point the renderer at an existing Chromium build.",
    "hyperframes": "Run `npx hyperframes --help` once inside the project to install the CLI, "
    "or rely on scripts/render-browser.mjs (puppeteer-core) as fallback.",
    "coli": "Install the coli CLI (ASR/TTS adapter). Optional: captions can also come from "
    "a --words-json file.",
}


def run(cmd: list[str], timeout: float = 20.0) -> tuple[bool, str]:
    """Run a command, returning (ok, first useful stdout/stderr line)."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    out = (proc.stdout or proc.stderr or "").strip().splitlines()
    detail = out[0].strip() if out else f"exit {proc.returncode}"
    return proc.returncode == 0, detail


def check_python3() -> tuple[bool, str]:
    ok, detail = run([sys.executable or "python3", "--version"])
    if ok and not shutil.which("python3"):
        return ok, f"{detail} (python3 not on PATH, using {sys.executable})"
    return ok, detail


def check_binary(name: str, args: list[str] | None = None) -> tuple[bool, str]:
    path = shutil.which(name)
    if not path:
        return False, "not found on PATH"
    return run([path, *(args or ["--version"])])


def check_chrome() -> tuple[bool, str]:
    found = shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium")
    candidates: list[str] = ([found] if found else []) + list(CHROME_CANDIDATES)
    for path in candidates:
        binary = Path(path).expanduser()
        if binary.exists():
            ok, detail = run([str(binary), "--version"], timeout=15)
            return ok, detail if ok else str(binary)
    return False, "no Chrome/Chromium binary found in standard locations"


def check_hyperframes() -> tuple[bool, str]:
    npx = shutil.which("npx")
    if not npx:
        return False, "npx not found (install Node.js first)"
    ok, detail = run([npx, "--no-install", "hyperframes", "--version"], timeout=20)
    if ok:
        return True, detail
    return False, "hyperframes not installed for npx (probe timed out after 20s or not found)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the knowledge-motion toolchain.")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args()

    checks: list[dict[str, object]] = []
    for name, fn in (
        ("python3", check_python3),
        ("node", lambda: check_binary("node")),
        ("ffmpeg", lambda: check_binary("ffmpeg", ["-version"])),
        ("ffprobe", lambda: check_binary("ffprobe", ["-version"])),
        ("chrome", check_chrome),
        ("hyperframes", check_hyperframes),
        ("coli", lambda: check_binary("coli", ["--help"])),
    ):
        ok, detail = fn()
        checks.append(
            {
                "name": name,
                "ok": ok,
                "detail": detail,
                "core": name in ("ffmpeg", "ffprobe"),
                "suggestion": "" if ok else SUGGESTIONS[name],
            }
        )

    core_ok = all(entry["ok"] for entry in checks if entry["core"])

    if args.json:
        print(json.dumps({"coreReady": core_ok, "checks": checks}, ensure_ascii=False, indent=2))
    else:
        width = max(len(str(entry["name"])) for entry in checks) + 2
        print(f"{'CHECK'.ljust(width)}STATUS   DETAIL")
        for entry in checks:
            status = "ok" if entry["ok"] else "MISSING"
            print(f"{str(entry['name']).ljust(width)}{status.ljust(8)} {entry['detail']}")
            if entry["suggestion"]:
                print(f"{''.ljust(width)}         -> {entry['suggestion']}")
        verdict = "READY" if core_ok else "NOT READY"
        print(f"\ncore (ffmpeg/ffprobe): {verdict}")

    raise SystemExit(0 if core_ok else 1)


if __name__ == "__main__":
    main()
