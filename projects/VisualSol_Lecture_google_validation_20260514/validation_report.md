# Validation Report

Generated PPTX:

- `exports/VisualSol_google_validation_20260514.pptx`

## Checks

- PPTX loads with `python-pptx`: pass
- Slide count: 6
- `ppt/presentation.xml`: present
- `ppt/slideMasters/slideMaster1.xml`: present
- Top master inherited VisualSol SVG glow: no
- VisualSol purple token `#7C3AED`: absent
- VisualSol blue token `#1E40AF`: absent
- Title layout has cover placeholders: pass
- Section layout has section placeholders: pass
- Title layout content accent: absent
- Section layout content accent: absent
- Content layout accent: present
- Layout placeholder dashed borders: absent
- Ending slide literal `06 / 06`: absent
- Ending slide `data-slot="slide.6"` text: absent from PPTX XML
- `Microsoft YaHei` fallback: absent
- `lang="zh-CN"`: absent
- Arial typography: present

## Result

The master/layout fixes generalize to this alternate Google-style validation
deck. The important regression guard added during this run is that master glows
are now derived from actual SVG radial gradients; templates without such glows
do not inherit VisualSol-specific dark glows.
