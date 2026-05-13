# Research Dark Template - Design Specification

> Cinematic dark research presentation template modelled on the Poppins + Lato typographic system from `Research_presen_dark.pptx`. Suited for CVPR-style technical talks, AI method papers, architecture briefings, and benchmark-heavy presentations.

## I. Template Overview

- Template ID: `research_dark`
- Display name: Research Dark Template
- Category: scenario
- Use cases: CVPR / NeurIPS / ECCV paper talks, AI research briefings, architecture summaries, benchmark decks, lab seminars, technical product research updates
- Design tone: cinematic, technical, high-contrast, editorial, breathing
- Theme mode: Dark (near-black background + purple accent)
- Canvas format: ppt169 (1280 × 720 px)
- Reference source: `examples_other_source/Research_presen_dark.pptx`

## II. Canvas Specification

- viewBox: `0 0 1280 720`
- Width: 1280 px
- Height: 720 px
- Safe margin: 60 px on all sides (title left edge: 81 px)
- Footer zone: y 650–700

## III. Color Scheme

| Role | HEX | Usage |
|------|-----|-------|
| Background | `#05050A` | Slide base fill |
| Panel / card | `#0D0D14` | Secondary dark surface |
| Purple primary | `#A855F7` | Key accent, highlights, labels |
| Purple secondary | `#C084FC` | Sub-headings, callouts |
| Purple glow | `#7C3AED` | Background radial gradient |
| Title text | `#FFFFFF` | All-caps slide titles, main text |
| Body text | `#94A3B8` | Body copy, descriptions (Slate-400) |
| Muted / footer | `#64748B` | Footer, captions, de-emphasised |
| Indigo link | `#4F46E5` | URLs, links |

## IV. Typography System

| Role | Font | Weight | Size (px) | Color |
|------|------|--------|-----------|-------|
| Slide title (ALL CAPS) | Poppins, Arial, sans-serif | 700 | 43 | `#FFFFFF` |
| Chapter title | Poppins, Arial, sans-serif | 700 | 72 | `#FFFFFF` |
| Cover main title | Poppins, Arial, sans-serif | 700 | 68–80 | `#FFFFFF` |
| Big stat / number | Poppins, Arial, sans-serif | 700 | 96–120 | `#A855F7` |
| Sub-heading | Poppins, Arial, sans-serif | 700 | 30 | `#C084FC` |
| Body text | Lato, Arial, sans-serif | 400 | 19 | `#94A3B8` |
| Body bold / label | Lato, Arial, sans-serif | 700 | 19 | `#FFFFFF` |
| Caption | Lato, Arial, sans-serif | 400 | 16 | `#64748B` |
| Cover category label | Poppins, Arial, sans-serif | 700 | 13 | `#A855F7` |
| Cover subtitle | Lato, Arial, sans-serif | 400 | 26 | `#FFFFFF` |
| Cover author | Poppins, Arial, sans-serif | 400 | 17 | `#94A3B8` |

## V. Page Structure

### Shared Background

Every slide uses the same base background:
```
<rect x="0" y="0" width="1280" height="720" fill="#05050A"/>
<rect x="0" y="0" width="1280" height="720" fill="url(#bgGlow)"/>  <!-- radial purple glow, top-right -->
<rect x="0" y="0" width="1280" height="3" fill="#A855F7"/>          <!-- 3 px top accent bar -->
```

### Content Page Header Zone (y 0–140)

- Top bar: 3 px, full-width, `#A855F7`
- Title: ALL-CAPS Poppins 43 px bold `#FFFFFF`, x=81, baseline y=100
- Thin title underline: 1 px, `#A855F7` opacity 0.2, x=81 to x=1199, y=118

### Content Area (y 140–640)

- Flexible zone for Executor
- Left margin: 60 px, right margin: 60 px
- Typical card padding: 24 px internal, 20 px gap between cards
- Corner radius: 10–14 px

### Footer Zone (y 640–700)

- Optional thin divider at y=650, `#1E1E2E`, 1 px
- Source text: x=81, y=675, Lato 13 px, `#64748B`
- Page number: x=1199, y=675, text-anchor=end, Lato 13 px, `#64748B`

## VI. Page Types

| File | Purpose |
|------|---------|
| `01_cover.svg` | Cover — title, subtitle, author, date, centred |
| `02_toc.svg` | Table of contents — chapter list |
| `02_chapter.svg` | Chapter divider — large chapter title |
| `03_content.svg` | Generic content — ALL-CAPS title + flexible body |
| `04_ending.svg` | Ending — thank-you message, contact |

## VII. Layout Modes (Recommended)

| Mode | Description | Trigger |
|------|-------------|---------|
| `full-figure` | Full-width image (y 140–620) + caption below | Image-heavy method/result slides |
| `half-split` | Left text (w=540) + right image (w=620) | System overview, method components |
| `three-column` | 3 × 360 px columns | 3-point comparisons, ablation factors |
| `big-stat` | Large metric number (Poppins 96–120 px) + description right | Dataset scale, benchmark score highlights |
| `two-panel` | 2 × 540 px panels | Prior-method comparisons, pros/cons |
| `quote` | Large centred quote with decorative large `"` | Pull-quote / transition slides |

## VIII. Spacing Specification

| Element | Value |
|---------|-------|
| Left / right margin | 60–81 px |
| Title left indent | 81 px |
| Gap between title underline and first content | 22–32 px |
| Card internal padding | 24 px |
| Card corner radius | 10–14 px |
| Inter-card gap | 20–24 px |
| Footer offset above bottom | 45 px |

## IX. SVG Technical Constraints

- viewBox: `0 0 1280 720` (mandatory)
- Backgrounds: `<rect>` fills only — no `<image>` for backgrounds in templates
- Text wrapping: `<tspan dy="...">` (relative offset only)
- Transparency: `fill-opacity` / `stroke-opacity` (no `rgba()`)
- Gradients: `<defs>` with `<linearGradient>` or `<radialGradient>`
- No: `<foreignObject>`, `clipPath` on shapes/text, `mask`, `<style>`/`class`, `textPath`, `animate*`, `script`
- No HTML named entities (`&nbsp;` → use raw Unicode space; `&mdash;` → `—`)

## X. Placeholder Specification

### Cover
| Placeholder | Content |
|-------------|---------|
| `{{TITLE}}` | Main title (large) |
| `{{SUBTITLE}}` | Tagline / paper title |
| `{{AUTHOR}}` | Authors / institution |
| `{{DATE}}` | Date / conference / venue |

### Chapter
| Placeholder | Content |
|-------------|---------|
| `{{CHAPTER_NUM}}` | Chapter number (e.g. 01, 02) |
| `{{CHAPTER_TITLE}}` | Chapter title text |
| `{{CHAPTER_TITLE_EN}}` | Optional English subtitle |

### Content
| Placeholder | Content |
|-------------|---------|
| `{{PAGE_TITLE}}` | ALL-CAPS slide title |
| `{{CONTENT_AREA}}` | Flexible body — replaced by Executor |
| `{{SOURCE}}` | Footer source note |
| `{{PAGE_NUM}}` | Page number |

### TOC
| Placeholder | Content |
|-------------|---------|
| `{{TOC_ITEM_1_TITLE}}` — `{{TOC_ITEM_N_TITLE}}` | Chapter titles |
| `{{TOC_ITEM_1_DESC}}` — `{{TOC_ITEM_N_DESC}}` | Optional short descriptions |

### Ending
| Placeholder | Content |
|-------------|---------|
| `{{THANK_YOU}}` | Thank-you heading |
| `{{ENDING_SUBTITLE}}` | Closing sub-message |
| `{{CONTACT_INFO}}` | Contact / links |

## XI. Usage Guide

- Executor should write ALL slide titles in ALL CAPS to match the template convention.
- Sub-headings use Poppins bold `#C084FC`; body text uses Lato `#94A3B8`.
- Dark card panels (`#0D0D14`, optional `#151520`) may be used freely in the content area.
- Purple (`#A855F7`) is the primary accent — use sparingly for highlights and key numbers.
- Avoid horizontal footer lines unless using a metric-heavy or table layout where a separator aids readability.
- For image-heavy slides, use a full-width `<image>` with `preserveAspectRatio="xMidYMid slice"` and a `fill-opacity="0.15"` dark overlay rect on top.
