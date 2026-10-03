# Style preset: editorial paper (default)

A warm, print-magazine look for graphic interludes: tactile paper background, black ink, one strong accent. It reads as "designed by a person", which is the point — it avoids the neon-purple AI aesthetic that audiences now scroll past.

Use this when the user has no `brand.md` and didn't describe a style. Unbranded by default: no logo, watermark, organization name or URL unless the user supplies them.

## Palette

```css
--paper:       #E9E0D3;  /* main interlude background */
--paper-dark:  #D4C8B8;  /* shapes, dividers */
--paper-light: #F6F0E7;  /* cards */
--cream:       #FFFDF7;  /* caption text on footage */
--ink:         #1B1D1E;  /* headlines, objects */
--ink-soft:    #3A3D3E;  /* supporting text */
--accent:      #E66A21;  /* burnt orange: the one emphasized word/element */
--accent-dark: #C85218;
--accent-2:    #2A8791;  /* muted teal: rare secondary accent */
--accent-2-dark: #216A72;
--micro:       #D8A44A;  /* muted gold: tiny details only */
```

Hierarchy: paper/cream/ink dominate; orange marks the single most important thing on screen; teal appears occasionally; gold almost never. Small hue shifts to harmonize with the footage are fine — keep the roles.

## Interlude scenes

- Background: `--paper`, optionally with subtle grain (local asset only).
- One monochrome ink object/diagram as the focal point, drawn in SVG where possible.
- Type: one oversized keyword (heavy weight, often in `--accent`), one short supporting line in `--ink-soft`. Extreme but controlled size contrast.
- Build in sync with speech → hold → hard cut out.

## On footage

- Captions in `--cream`, emphasis word in `--accent`, prior words may dim to ~50% opacity.
- Color correction stays natural; the style lives in the graphics, not in a heavy grade on the face.

## Avoid

Neon gradients, rainbow palettes, heavy glassmorphism, glossy corporate templates, and stock "AI" imagery.

## Writing another preset

Copy this file, keep the same headings (Palette with roles, Interlude scenes, On footage, Avoid), and point the brief at it. A preset is a set of concrete, checkable rules — "captions 64% down, cream, one orange word" — not adjectives like "modern" or "clean".
