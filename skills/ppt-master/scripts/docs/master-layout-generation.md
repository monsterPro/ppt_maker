# Master Layout Generation

`svg_to_pptx.py` should derive PowerPoint masters/layouts from the generated
SVG deck archetypes, not from ad-hoc manual adjustments.

## Principle

Treat the SVG deck as the visual source of truth:

- **Top Slide Master**: deck-wide background, theme text styles, footer, slide
  number, and visible style placeholders.
- **Title Slide layout**: cover/title archetype. No content-slide header accent.
  Include centered category, short divider, title, subtitle, and author/date
  placeholders based on the cover SVG.
- **Section Header layout**: chapter divider archetype. No content-slide header
  accent. Include centered chapter label, short divider, section title, and
  subtitle placeholders based on the section SVG.
- **Content layouts**: regular slide archetype. Mirror the SVG header chrome:
  left accent bar, title textbox position, and underline.
- **Blank layout**: keep clean for generated slides that already carry their own
  SVG-derived shapes.
- **Placeholders**: should inherit font/color/position styles, but should not
  draw visible dashed borders. PowerPoint may show selection handles while
  editing; the OOXML shape line itself should be `noFill`.
- **Master-managed footer/page numbers**: generated slide SVGs may contain
  legacy footer groups or standalone bottom-right page-number text. The native
  converter must skip these, because the Slide Master owns footer text and slide
  numbers.
- **Master glows**: derive radial glow geometry from SVG `radialGradient`
  parameters. For object-bounding-box gradients, convert `cx`, `cy`, and `r`
  into an ellipse whose center and radii are scaled by the slide width/height.
  Do not approximate this with an arbitrary ellipse.

One top Slide Master cannot exactly represent multiple SVG background variants
with different glow centers, radii, or stop opacities. If exact per-archetype
background matching is required, move background glows to the corresponding
slide layouts or keep the SVG background on generated slides.

Do not put archetype-specific chrome on the top Slide Master. Anything placed
there is inherited by title and section layouts, which makes the layouts drift
from their SVG archetypes.

## Current Detection Model

The integrated implementation in `scripts/svg_to_pptx/pptx_master.py` uses the
default `python-pptx` layout numbers:

- `slideLayout1.xml`: Title Slide
- `slideLayout3.xml`: Section Header
- `slideLayout7.xml`: Blank
- all other layouts: content-style layouts

Content-style layouts receive the standard header chrome. Title, section, and
blank layouts do not.

## Expected Content Header Geometry

For a 1280 x 720 SVG canvas, regular content slides use:

```xml
<rect x="60" y="67" width="3" height="40" fill="#A855F7"/>
<text x="81" y="100" font-size="43" font-family="Poppins, Arial, sans-serif">...</text>
<rect x="81" y="118" width="1118" height="1" fill="#A855F7" fill-opacity="0.20"/>
```

The master layout geometry should be computed by scaling these SVG coordinates
to EMU units. Do not tune these by eye in PowerPoint.

## Update Procedure

When a deck exposes a mismatch between generated slides and master layouts:

1. Scan `svg_final/` for representative archetypes: cover/title, section
   dividers, regular content pages, and any special page family.
2. Compare repeated SVG chrome coordinates across the archetype. Prefer the
   majority pattern; fix outlier SVGs when one slide differs accidentally.
3. Put only deck-wide elements on the top Slide Master.
4. Put archetype-specific chrome on the matching slide layouts.
5. Regenerate with:

```bash
python3 scripts/svg_to_pptx.py <project_path> -s final --only native -a none
```

6. Verify the PPTX package before opening:
   - `ppt/slideMasters/slideMaster1.xml` has no content-only chrome.
   - title and section layout XML files have no header accent shapes.
   - content layout XML files have the expected accent bar and underline.
   - layout placeholder shapes do not contain `a:prstDash` or visible line fill.
   - master glow shapes use `a:gradFill`, not a flat `a:solidFill`, and their
     geometry is derived from SVG `cx/cy/r` rather than tuned by eye.
   - generated slide XML does not contain literal bottom-right strings such as
     `26 / 26`; slide numbers should come from the master field.
   - generated slide XML still uses the intended font family and language tags.

## Future Automation

The next improvement should be a scanner that reads `svg_final/`, clusters pages
by visible chrome and `data-slot` names, and emits layout descriptors consumed
by `pptx_master.py`. That scanner should fail loudly when archetype coordinates
conflict instead of silently guessing.
