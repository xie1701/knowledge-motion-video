# Series furniture

Series furniture is the persistent packaging layer that makes a channel recognizable: top
title bar, bottom CTA, chapter progress, trust anchors. It is **independent of scene style** —
it renders above scene content, below burned-in narration subtitles, and can be toggled per
project without touching any scene contract.

## Layers (bottom to top)

1. Scene clips (per-route visual grammars)
2. Furniture layer (this document)
3. Burned-in captions (always last in FFmpeg)

## Elements

| Element | Placement | Notes |
|---|---|---|
| Series/title bar | top, inside safe area | date/episode + title, monospaced or brand font, muted color |
| Accent rule | under title bar | one 2–4px line, accent color, animates once per chapter, not per scene |
| Chapter progress | top or bottom edge | thin track + filled segments proportional to chapter durations |
| Trust anchor | fixed corner | avatar, logo, or handle; static; never overlaps scene focal content |
| CTA strip | bottom, above caption band | static text or one entrance per film; keep clear of the caption safe area |
| End card | final 2–3 s | contact/subscribe/info; replaces CTA strip, never covers the caption band |

## Rules

- Furniture occupies the outer 6–8% of the frame (portrait) or the top/bottom bands (landscape).
  Scene safe areas in `scenes.json` must already exclude these bands.
- Furniture animates at most once per chapter (entrance) plus the progress fill. Per-scene
  furniture motion reads as noise.
- Contrast: furniture text must pass WCAG AA against the scene background across all scenes of
  the film; when scene backgrounds vary, put furniture text on a translucent backing plate.
- Furniture is declared once per project (`project.furniture` in a composition config or a
  dedicated full-duration clip at the highest `data-track-index` below captions), not per scene.

## Reusable fragment

`assets/templates/furniture/standard.html` implements the standard set (title bar, accent rule,
progress track, corner anchor, CTA strip) as a single full-duration clip with placeholder
tokens (`{{SERIES}}`, `{{EPISODE}}`, `{{TITLE}}`, `{{CTA}}`, `{{CHAPTERS}}`) and a deterministic
GSAP timeline driven by chapter start times.
