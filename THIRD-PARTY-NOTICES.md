# Third-party notices

This project is MIT licensed (see [LICENSE](LICENSE)). The components below keep their own
terms — verify against upstream before relying on this summary.

- **GSAP** — vendored into compositions at `composition/vendor/gsap.min.js`: GreenSock Standard
  License. Free for general commercial use; restricted when building competing visual animation
  builder tools. Replace it with your own GSAP licence if your use falls outside those terms.
- **HyperFrames** (optional default renderer) — Apache-2.0.
- **FFmpeg** — LGPL-2.1+ / GPL depending on build configuration and enabled encoders.
- **Motion Canvas, Manim, Lottie-web, Revideo** — MIT.
- **Kokoro TTS** — Apache-2.0 (weights Apache-2.0; voice/G2P dependencies vary).
- **WhisperX** — BSD-2-Clause (alignment/diarization models have separate terms).
- **jieba `dict.txt`** — MIT, Copyright (c) 2013 Sun Junyi. `assets/lexicon/zh-words.txt` is
  derived from it: trimmed and extended with project-authored vocabulary. Provenance notes are in
  the file header.
- **Example assets** — the CC0 music bed and the CC BY-SA photo shipped under `examples/` carry
  their own licences; each one is recorded in that example's `assets/media/manifest.json`.

Anything you generate, download, or import with this pipeline is governed by its own license and
the terms of the service that produced it. Record provenance in `assets/media/manifest.json` and
verify before publishing.
