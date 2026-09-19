# Style samples

Four 10.4-second renders of the same script ("文案不是成片"), one per design preset,
each pairing a preset with the route that suits it best. Use them to preview the
visual grammar before committing a project to a route.

| Preset | Route | Entry point |
|---|---|---|
| clean-education | whiteboard-tutorial | [composition/index.html](clean-education/composition/index.html) |
| dark-technical | data-viz | [composition/index.html](dark-technical/composition/index.html) |
| warm-editorial | editorial-collage | [composition/index.html](warm-editorial/composition/index.html) |
| bold-social | kinetic-typography | [composition/index.html](bold-social/composition/index.html) |

Each directory is a minimal project:

```text
composition/index.html      self-contained composition (GSAP vendored, local fonts,
                            motion registered on window.__timelines)
storyboard/scenes.json      scene manifest validated by scripts/validate_scenes.py
renders/visual-master.mp4   rendered reference output (1080×1920, 30fps)
renders/style-loop.gif      looping preview
```

Re-render any of them:

```bash
cd examples/style-samples/<name>/composition
npx hyperframes render --output ../renders/visual-master.mp4 --fps 30
# or, without the HyperFrames CLI:
node ../../../scripts/render-browser.mjs composition/index.html --fps 30 \
  --output ../renders/visual-master.mp4
```

A side-by-side comparison lives at [`docs/style-comparison.gif`](../../docs/style-comparison.gif).

## Timing contract used by all samples

Scenes are 2.8s / 4.8s / 2.8s (build / breathe / resolve). The first element of
every scene enters within 0.2s of the scene boundary — never leave a scene's
opening frames on furniture alone. Nothing except the burned caption band lives
in the bottom 230px.
