# PPT Master Fork

Native-editable PowerPoint generation workflow with improved SVG-to-PPTX master
slide support.

This fork keeps the original PPT Master idea: generate a deck as SVG first, then
export a real `.pptx` made of editable PowerPoint shapes and text boxes. The
local changes focus on making exported decks easier to maintain in PowerPoint:
Slide Master layouts, reusable placeholders, correct fonts, master-managed page
numbers, and cleaner text boxes.

## What This Fork Adds

- Integrated Slide Master generation in `scripts/svg_to_pptx/pptx_master.py`.
- Title, section, content, and blank layouts derived from SVG archetypes.
- Master-managed footer and slide numbers.
- Standalone generated page-number text is skipped during native export.
- Placeholder text boxes no longer have visible dashed borders.
- Font fallback no longer forces Latin text into `Microsoft YaHei`.
- Text run language is inferred from actual text content.
- SVG bullet hints can become native PowerPoint bullets.
- Master radial glows are derived from actual SVG gradients, not hardcoded.
- Slides text-layer helper scripts for text-only edits.

## Repository Layout

```text
ppt-master/
  AGENTS.md                         canonical agent instructions
  CLAUDE.md                         pointer to AGENTS.md
  README.md                         this file
  requirements.txt                  Python dependencies
  skills/ppt-master/                main skill, scripts, templates, references
  skills/ppt-master/scripts/        command-line tools
  skills/ppt-master/scripts/docs/   script and master-layout documentation
  projects/                         local generated projects, git-ignored
  docs/archive/                     historical implementation notes
```

Important implementation docs:

- `skills/ppt-master/scripts/docs/svg-pipeline.md`
- `skills/ppt-master/scripts/docs/master-layout-generation.md`
- `skills/ppt-master/references/slides-text-layer.md`
- `skills/ppt-master/references/textbox-consolidation.md`

## Setup

Use Python 3.10 or newer.

```bash
cd ppt-master
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
cd ppt-master
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

If the virtual environment already exists, use it directly:

```bash
.venv\Scripts\python -m compileall skills/ppt-master/scripts/svg_to_pptx
```

## Basic Usage

Generate a native editable PPTX from a project with finalized SVG files:

```bash
.venv\Scripts\python skills/ppt-master/scripts/svg_to_pptx.py projects/<project_name> -s final --only native -a none
```

Recommended project structure:

```text
projects/<project_name>/
  spec_lock.md
  design_spec.md
  svg_output/
  svg_final/
  slides/
  notes/
  exports/
```

The exporter reads `svg_final/` when `-s final` is used. The output goes to
`exports/` by default unless `-o` is supplied.

Explicit output example:

```bash
.venv\Scripts\python skills/ppt-master/scripts/svg_to_pptx.py ^
  projects/VisualSol_Lecture_ppt169_20260504 ^
  -s final --only native -a none ^
  -o projects/VisualSol_Lecture_ppt169_20260504/exports/VisualSol_Lecture_final.pptx
```

## Text-Only Editing

For wording changes, use the slides text layer instead of editing SVG by hand:

```bash
.venv\Scripts\python skills/ppt-master/scripts/slides_extract.py projects/<project_name>
# edit projects/<project_name>/slides/*.md
.venv\Scripts\python skills/ppt-master/scripts/slides_apply.py projects/<project_name>
.venv\Scripts\python skills/ppt-master/scripts/svg_to_pptx.py projects/<project_name> -s final --only native -a none
```

For older projects without `data-slot` markers:

```bash
.venv\Scripts\python skills/ppt-master/scripts/slides_init.py projects/<project_name>
.venv\Scripts\python skills/ppt-master/scripts/slides_extract.py projects/<project_name>
```

## Validation Decks

The local workspace currently includes two useful validation projects under
`projects/`:

- `VisualSol_Lecture_ppt169_20260504`
- `VisualSol_Lecture_google_validation_20260514`

`projects/` is intentionally ignored by git. Keep these locally, or force-add a
specific project only if you want to publish generated examples.

Current final VisualSol export:

```text
projects/VisualSol_Lecture_ppt169_20260504/exports/VisualSol_Lecture_20260514_svg_glowmatch.pptx
```

Google-style validation export:

```text
projects/VisualSol_Lecture_google_validation_20260514/exports/VisualSol_google_validation_20260514.pptx
```

## Verification Commands

Run these before committing:

```bash
git status --short
.venv\Scripts\python -m compileall skills/ppt-master/scripts/svg_to_pptx
.venv\Scripts\python skills/ppt-master/scripts/svg_to_pptx.py projects/VisualSol_Lecture_google_validation_20260514 -s final --only native -a none
```

Useful PPTX XML checks can be done with Python `zipfile` if PowerPoint is not
available. The validation project has a short report at:

```text
projects/VisualSol_Lecture_google_validation_20260514/validation_report.md
```

## Notes

- Do not commit `.venv/`, temporary build folders, or PowerPoint lock files.
- Generated project folders are ignored by default because they can grow large.
- Keep `AGENTS.md` as the canonical instructions file for coding agents.

## Original Source

This repository is a fork of the original PPT Master source code:

```text
https://github.com/hugohe3/ppt-master
```

Local changes in this fork focus on editable PPTX export, Slide Master support,
template validation, and workflow cleanup.

## License

This repository keeps the original MIT license. See `LICENSE`.
