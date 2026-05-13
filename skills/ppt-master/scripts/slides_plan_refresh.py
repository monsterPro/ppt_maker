#!/usr/bin/env python3
"""PPT Master - Slides Text Layer: refresh derivable sections of slides/_plan.md

One-way derive (slides/*.md -> slides/_plan.md). Updates the parts of the plan
that mirror per-slide MD content:

  * §4 "Chapter Structure" table: Ch / Title / Slides columns
  * §5 "Per-Slide Breakdown" tables: Title column for each slide row

Human-authored columns (Role, Net runtime, Rhythm, Time, Coverage) and entire
sections (narrative spine, transitions, risks, references, etc.) are NEVER
touched. This script is intentionally narrow.

The script never inserts or deletes rows automatically — it warns on
discrepancies (a slide present in slides/ but missing from §5, an extra row
in §5 with no matching slide). The user resolves by editing _plan.md.

Usage:
    python scripts/slides_plan_refresh.py <project_path>
    python scripts/slides_plan_refresh.py <project_path> --check  # report intended writes only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from collections import OrderedDict

# Make stdout/stderr tolerant of non-UTF-8 Windows consoles (cp949, cp1252, ...)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


PLAN_FILENAME = "_plan.md"
SLOT_LINE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\-]*)\s*:\s*(.*)$")
SLIDE_NAME = re.compile(r"^(\d+)_")
H2_LINE = re.compile(r"^\s*##\s+(.+?)\s*$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")


# ---------- Slide MD parsing (mirrors slides_apply.py) ----------

def parse_slides_md(md_path: Path) -> "OrderedDict[str, str]":
    slots: OrderedDict[str, str] = OrderedDict()
    text = md_path.read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith(">"):
            continue
        m = SLOT_LINE.match(line)
        if not m:
            continue
        slots[m.group(1)] = m.group(2).strip()
    return slots


# ---------- Derive view of slides/ ----------

def derive_slide_view(slides_dir: Path) -> "OrderedDict[int, dict]":
    """For each slides/NN_*.md (excluding files starting with '_'), build a view:

    {
        slide_num: {
            'name': filename stem,
            'slots': OrderedDict[str, str],
            'title': str | None,        # bare title for use in §4 / §5 cells
            'is_chapter_divider': bool,
            'ch_num': int | None,       # parsed from chapter-number.1 like 'CHAPTER 03'
            'ch_subtitle': str | None,
        }
    }
    """
    view: "OrderedDict[int, dict]" = OrderedDict()
    for md_path in sorted(slides_dir.glob("*.md")):
        if md_path.name.startswith("_"):
            continue
        m = SLIDE_NAME.match(md_path.name)
        if not m:
            continue
        slide_num = int(m.group(1))
        slots = parse_slides_md(md_path)

        ch_title = slots.get("chapter-title.1")
        ch_number = slots.get("chapter-number.1")
        ch_subtitle = slots.get("chapter-subtitle.1")
        ch_num: int | None = None
        if ch_number:
            num_m = re.search(r"\d+", ch_number)
            ch_num = int(num_m.group()) if num_m else None

        # Choose a single 'title' string for derivation. Priority:
        #   chapter-title.1 -> main-title.1 -> header.1 -> first 'slide.*' value
        title = (
            ch_title
            or slots.get("main-title.1")
            or slots.get("header.1")
            or next((v for k, v in slots.items() if k.startswith("slide.")), None)
        )

        view[slide_num] = {
            "name": md_path.stem,
            "slots": slots,
            "title": title,
            "is_chapter_divider": ch_title is not None,
            "ch_num": ch_num,
            "ch_subtitle": ch_subtitle,
        }
    return view


# ---------- Chapter range computation ----------

def compute_chapters(view: "OrderedDict[int, dict]") -> list[dict]:
    """Group slides into chapters using chapter divider slides as boundaries.

    Sub-section dividers (slides whose chapter-number.1 either repeats a
    previously-seen ch_num or is None while chapter-title.1 still exists) are
    rolled into the most recent top-level chapter — they don't start a new
    chapter row in §4.
    """
    chapters: list[dict] = []
    seen_nums: set[int] = set()

    slide_nums_sorted = sorted(view.keys())
    # First pass: identify top-level chapter divider slides
    top_level_dividers: list[int] = []
    for n in slide_nums_sorted:
        s = view[n]
        if not s["is_chapter_divider"]:
            continue
        ch_num = s["ch_num"]
        # Treat as top-level only if it has a fresh ch_num
        if ch_num is None:
            continue
        if ch_num in seen_nums:
            continue  # repeated number = sub-section divider
        seen_nums.add(ch_num)
        top_level_dividers.append(n)

    # Build chapter rows with slide ranges
    for idx, start in enumerate(top_level_dividers):
        end = top_level_dividers[idx + 1] - 1 if idx + 1 < len(top_level_dividers) else slide_nums_sorted[-1]
        # Closing slides (e.g., 26_ending) are not part of a chapter conceptually,
        # but we'll cap end at "last content slide before any obvious closing".
        # Heuristic: if the LAST slide is anchor-like with no chapter-title and the
        # filename suggests an ending, exclude it.
        s_start = view[start]
        chapters.append({
            "ch_num": s_start["ch_num"],
            "ch_title": s_start["title"] or "",
            "start": start,
            "end": end,
        })

    # If the final chapter ends past the last slide that has a chapter-title /
    # is part of the chapter, trim trailing "ending"-style slides.
    if chapters:
        last = chapters[-1]
        # walk back from last['end'] until a slide that is plausibly part of the chapter
        n = last["end"]
        while n > last["start"]:
            s = view.get(n)
            if not s:
                n -= 1
                continue
            name = s["name"].lower()
            # Treat names like '26_ending' as outside the chapter
            if "ending" in name or "thank" in name:
                n -= 1
                continue
            break
        last["end"] = n

    return chapters


# ---------- Markdown table editing ----------

def split_md_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def join_md_row(cols: list[str]) -> str:
    return "| " + " | ".join(cols) + " |"


def is_separator_row(cols: list[str]) -> bool:
    if not cols:
        return False
    return all(re.match(r"^:?-+:?$", c.strip()) for c in cols if c.strip())


def find_section(lines: list[str], heading_starts_with: str) -> tuple[int, int] | None:
    """Return [start, end) line indices for the H2 section whose heading begins with
    `heading_starts_with` (e.g., '4. Chapter Structure'). Returns None if not found.
    The end is the index of the next H2 (or len(lines))."""
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        m = H2_LINE.match(line)
        if not m:
            continue
        title = m.group(1)
        if start is None and title.startswith(heading_starts_with):
            start = i
            continue
        if start is not None:
            end = i
            break
    if start is None:
        return None
    return start, end


def iter_tables(lines: list[str], section: tuple[int, int]):
    """Yield (header_idx, sep_idx, body_start_idx, body_end_idx) for each table
    inside the given line span. body_end is exclusive."""
    s, e = section
    i = s
    while i < e:
        line = lines[i]
        if TABLE_ROW.match(line):
            header_idx = i
            # Header followed by separator
            if i + 1 < e and TABLE_ROW.match(lines[i + 1]) and is_separator_row(split_md_row(lines[i + 1])):
                sep_idx = i + 1
                body_start = i + 2
                j = body_start
                while j < e and TABLE_ROW.match(lines[j]):
                    j += 1
                yield header_idx, sep_idx, body_start, j
                i = j
                continue
        i += 1


# ---------- Update logic ----------

def update_chapter_structure(lines: list[str], chapters: list[dict]) -> tuple[bool, list[str]]:
    """Find §4 table and update Ch / Title / Slides columns. Returns (changed, warnings)."""
    warnings: list[str] = []
    section = find_section(lines, "4. Chapter Structure")
    if section is None:
        return False, ["Section '4. Chapter Structure' not found; skipping."]

    tables = list(iter_tables(lines, section))
    if not tables:
        return False, ["No table found inside §4; skipping."]

    header_idx, sep_idx, body_start, body_end = tables[0]
    header_cols = split_md_row(lines[header_idx])
    if len(header_cols) < 3:
        return False, ["§4 table has fewer than 3 columns; skipping."]

    # Map ch_num -> chapter dict
    by_num = {c["ch_num"]: c for c in chapters if c["ch_num"] is not None}

    changed = False
    seen_nums: set[int] = set()
    for row_idx in range(body_start, body_end):
        cols = split_md_row(lines[row_idx])
        if len(cols) != len(header_cols):
            warnings.append(f"§4 row {row_idx + 1}: column count {len(cols)} != header {len(header_cols)}; skipping row")
            continue
        # Parse the chapter number from col 0
        num_m = re.search(r"\d+", cols[0])
        if not num_m:
            continue
        ch_num = int(num_m.group())
        seen_nums.add(ch_num)
        ch = by_num.get(ch_num)
        if ch is None:
            warnings.append(f"§4 has Ch {ch_num:02d} but no matching chapter divider in slides/")
            continue
        new_title = ch["ch_title"]
        new_slides = f"{ch['start']:02d}–{ch['end']:02d}"
        # Title cell: only overwrite if the slide-side chapter title is NOT
        # already a substring of the existing cell. This preserves richer
        # plan-side decoration like "World Models & Outlook" when the slide's
        # bare chapter-title is just "World Models".
        title_changed = False
        if new_title and new_title.lower() not in cols[1].lower():
            cols[1] = new_title
            title_changed = True
        slides_changed = cols[2] != new_slides
        if slides_changed:
            cols[2] = new_slides
        if title_changed or slides_changed:
            new_line = join_md_row(cols)
            if new_line != lines[row_idx]:
                lines[row_idx] = new_line
                changed = True

    # Warn about chapters in slides/ but not in §4
    for n in by_num:
        if n not in seen_nums:
            warnings.append(f"Ch {n:02d} exists in slides/ but no row in §4; not auto-inserting")

    return changed, warnings


def derive_title_cell(slide_num: int, slide: dict, existing_cell: str) -> str:
    """Compute the new value for the §5 'Title' cell.

    Strategy (conservative — never fabricate, never duplicate):
      1. If the slide has no derivable title -> leave cell alone.
      2. If the slide's title is already a (case-insensitive) substring of the
         existing cell -> leave it alone. The cell already mentions the title;
         the surrounding decoration (prefix / italic tagline / suffix) is the
         user's intentional formatting.
      3. Else if the cell contains italic *...* content -> replace ONLY the
         italic portion with the slide's title.
      4. Else -> leave cell alone (do NOT auto-fill bare cells; the user wrote
         them deliberately, e.g. "Chapter 04 divider", "Thank You / Questions").
    """
    new_title = slide.get("title")
    if not new_title:
        return existing_cell

    if new_title.lower() in existing_cell.lower():
        return existing_cell

    italic_match = re.search(r"\*([^*]+)\*", existing_cell)
    if italic_match:
        return existing_cell[:italic_match.start(1)] + new_title + existing_cell[italic_match.end(1):]

    # Non-italic, no title-substring match: don't touch.
    return existing_cell


def update_per_slide_tables(lines: list[str], view: "OrderedDict[int, dict]") -> tuple[bool, list[str]]:
    """Find §5 tables and update Title column per row, matching by slide #."""
    warnings: list[str] = []
    section = find_section(lines, "5. Per-Slide Breakdown")
    if section is None:
        return False, ["Section '5. Per-Slide Breakdown' not found; skipping."]

    changed = False
    seen_slides: set[int] = set()
    for header_idx, sep_idx, body_start, body_end in iter_tables(lines, section):
        header_cols = split_md_row(lines[header_idx])
        if len(header_cols) < 2:
            continue
        # Find the index of the title column (look for a column header containing 'title' or 'Role / Coverage'-ish wording)
        title_col_idx = 1  # convention: col 1 is the slide title in our §5 tables
        for row_idx in range(body_start, body_end):
            cols = split_md_row(lines[row_idx])
            if len(cols) != len(header_cols):
                warnings.append(f"§5 row {row_idx + 1}: column count {len(cols)} != header {len(header_cols)}; skipping row")
                continue
            num_m = re.match(r"^\s*(\d+)\s*$", cols[0])
            if not num_m:
                continue
            slide_num = int(num_m.group(1))
            seen_slides.add(slide_num)
            slide = view.get(slide_num)
            if slide is None:
                warnings.append(f"§5 row references slide {slide_num:02d} but no matching file in slides/")
                continue
            new_cell = derive_title_cell(slide_num, slide, cols[title_col_idx])
            if new_cell != cols[title_col_idx]:
                cols[title_col_idx] = new_cell
                new_line = join_md_row(cols)
                if new_line != lines[row_idx]:
                    lines[row_idx] = new_line
                    changed = True

    # Warn about slides not represented in §5
    for n in view:
        if n not in seen_slides:
            warnings.append(f"slide {n:02d} ({view[n]['name']}) exists in slides/ but no row in §5; not auto-inserting")

    return changed, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", help="Path to the PPT project directory")
    ap.add_argument("--check", action="store_true", help="Report intended writes; do not modify files")
    args = ap.parse_args()

    project = Path(args.project_path).resolve()
    slides_dir = project / "slides"
    plan_path = slides_dir / PLAN_FILENAME

    if not slides_dir.is_dir():
        print(f"Error: slides/ not found under {project}", file=sys.stderr)
        return 1
    if not plan_path.exists():
        print(f"Error: {plan_path} not found. Move/create it first.", file=sys.stderr)
        return 1

    print(f"[slides_plan_refresh] project: {project}")
    print(f"[slides_plan_refresh] target: {plan_path.relative_to(project)}")
    print(f"[slides_plan_refresh] mode: {'check' if args.check else 'write'}")
    print()

    view = derive_slide_view(slides_dir)
    if not view:
        print(f"[slides_plan_refresh] no slide MDs found under {slides_dir}", file=sys.stderr)
        return 1
    chapters = compute_chapters(view)

    print(f"[slides_plan_refresh] {len(view)} slide(s); {len(chapters)} chapter(s) detected:")
    for c in chapters:
        print(f"  Ch {c['ch_num']:02d}: {c['ch_title']!r}  slides {c['start']:02d}–{c['end']:02d}")
    print()

    original = plan_path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=False)

    ch_changed, ch_warnings = update_chapter_structure(lines, chapters)
    rs_changed, rs_warnings = update_per_slide_tables(lines, view)

    for w in ch_warnings + rs_warnings:
        print(f"  warn: {w}")

    if not (ch_changed or rs_changed):
        print(f"\n[slides_plan_refresh] _plan.md already matches slides/; nothing to do.")
        return 0

    new_text = "\n".join(lines)
    # Preserve trailing newline if the original had one
    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"

    if args.check:
        print(f"\n[slides_plan_refresh] would update _plan.md (§4 changed: {ch_changed}, §5 changed: {rs_changed})")
    else:
        plan_path.write_text(new_text, encoding="utf-8")
        print(f"\n[slides_plan_refresh] wrote {plan_path.relative_to(project)} (§4 changed: {ch_changed}, §5 changed: {rs_changed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
