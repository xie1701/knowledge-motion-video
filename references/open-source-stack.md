# Open-source stack notes

Read the workspace research report when it is available. Core selection rules:

- HyperFrames: default deterministic HTML/SVG/Canvas/GSAP composition and automated checks. HyperFrames is Apache-2.0; GSAP uses its separate Standard License, so review the product boundary if building a competing visual animation editor.
- FFmpeg: final media assembly, audio, captions, encoding, probing.
- Motion Canvas (MIT) or Revideo (MIT): optional TypeScript animation/rendering scenes.
- Manim (MIT): optional mathematical and geometric scenes.
- Lottie-web and Rive runtimes (MIT): playback of separately licensed vector animation assets.
- Theatre.js: optional keyframe tooling; core is Apache-2.0 while Studio is AGPL-3.0.
- ViMax (MIT) or MoneyPrinterTurbo (MIT): architecture references and optional generated-media workflows, not precise diagram renderers.
- Kokoro (Apache-2.0): local TTS option; audit voice, G2P, and espeak dependencies separately.
- WhisperX (BSD-2-Clause): word alignment option; alignment and diarization models have separate terms.
- anything2explainer: excellent process reference, but its toolkit is PolyForm Noncommercial; do not copy it into a commercial codebase without permission.
- video_explainer: useful architecture reference, but no explicit repository license was found at research time; treat the code as all-rights-reserved.
- Remotion: capable renderer with a custom source-available license; verify organization eligibility and Company License requirements.

Separate four license layers:

1. orchestration/source code;
2. fonts, icons, photos, music, and stock media;
3. model weights;
4. hosted API/service terms and generated-output rights.

Never infer commercial permission from a GitHub repository being public.
