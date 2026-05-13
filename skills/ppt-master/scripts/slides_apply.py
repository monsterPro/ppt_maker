#!/usr/bin/env python3
"""PPT Master - Slides Text Layer: apply slides/*.md back into SVG

Reads <project_path>/slides/*.md, parses the slot:value table, and rewrites
the inner text of every <text data-slot="..."> element in the matching
<project_path>/svg_output/*.svg file.

This is the slides -> SVG direction. After running, downstream commands
(finalize_svg.py / svg_to_pptx.py) reflect the new text content.

Usage:
    python scripts/slides_apply.py <project_path>
    python scripts/slides_apply.py <project_path> --check     # report intended changes only
    python scripts/slides_apply.py <project_path> --strict    # fail if any slot in MD is missing from SVG
"""

from __future__ import annotations

import argparse
import os
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

SLOT_LINE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\-]*)\s*:\s*(.*)$")


def parse_slides_md(md_path: Path) -> OrderedDict[str, str]:
    """Parse a slides/*.md file into an ordered slot:value mapping.

    Markdown headings (#, ##, ...), blockquotes (>), and blank lines are ignored.
    Lines matching `<slot.path>: <value>` define slots. Values are single-line.
    """
    slots: OrderedDict[str, str] = OrderedDict()
    text = md_path.read_text(encoding="utf-8")
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith(">"):
            continue
        m = SLOT_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        slots[key] = value
    return slots


def xml_escape_text(value: str) -> str:
    """Escape user-supplied text for safe insertion as XML element content."""
    # Order matters: & first.
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
    )


def apply_slots_to_svg_text(svg_text: str, slots: dict[str, str]) -> tuple[str, dict[str, bool]]:
    """Apply each slot to the SVG source text (regex-based, preserves formatting).

    Returns (new_svg_text, slot_found_map). slot_found_map[slot] is True if the
    slot was located and replaced, False if no matching <text data-slot=...> tag
    was found.
    """
    found: dict[str, bool] = {slot: False for slot in slots}
    new_text = svg_text

    for slot, value in slots.items():
        # Regex matches a single-line <text ... data-slot="SLOT" ...>...</text>
        # capturing the opening tag, the inner content, and the closing tag.
        pattern = re.compile(
            r'(<text\b[^>]*\bdata-slot="' + re.escape(slot) + r'"[^>]*>)'
            r'([^<]*)'
            r'(</text>)',
            flags=re.UNICODE,
        )
        replacement_inner = xml_escape_text(value)

        # Use a function for replacement to avoid backreference parsing of $/\
        def _repl(m, _inner=replacement_inner):
            return m.group(1) + _inner + m.group(3)

        new_text, n = pattern.subn(_repl, new_text)
        if n > 0:
            found[slot] = True
        # If the same slot somehow appears more than once we silently update all,
        # which is consistent with the "duplicate slot" warning surfaced by extract.

    return new_text, found


def find_pairs(svg_dir: Path, slides_dir: Path) -> list[tuple[Path, Path]]:
    """Return [(svg_path, md_path)] for every SVG that has a corresponding MD."""
    pairs: list[tuple[Path, Path]] = []
    for svg_path in sorted(svg_dir.glob("*.svg")):
        md_path = slides_dir / svg_path.with_suffix(".md").name
        if md_path.exists():
            pairs.append((svg_path, md_path))
    return pairs


def maybe_warn_on_dest_newer(svg_path: Path, md_path: Path) -> str | None:
    """Warn if SVG is newer than slides MD (apply would clobber SVG-side edits)."""
    if svg_path.stat().st_mtime > md_path.stat().st_mtime + 1.0:
        return (
            f"  ⚠️  '{svg_path.name}' is newer than '{md_path.name}' — "
            "the SVG already has edits not reflected in slides MD. "
            "Continuing will overwrite SVG text with MD values. "
            "Run slides_extract.py first if SVG-side edits should win."
        )
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", help="Path to the PPT project directory")
    ap.add_argument("--check", action="store_true", help="Report intended writes; do not modify files")
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero if any slot in slides/*.md does not map to a <text data-slot=...> in SVG")
    args = ap.parse_args()

    project = Path(args.project_path).resolve()
    svg_dir = project / "svg_output"
    slides_dir = project / "slides"

    if not svg_dir.is_dir():
        print(f"Error: svg_output/ not found under {project}", file=sys.stderr)
        return 1
    if not slides_dir.is_dir():
        print(f"Error: slides/ not found under {project}. "
              "Run slides_init.py + slides_extract.py first.", file=sys.stderr)
        return 1

    pairs = find_pairs(svg_dir, slides_dir)
    if not pairs:
        print(f"[slides_apply] no matching slides/*.md for SVG files under {svg_dir}", file=sys.stderr)
        return 1

    print(f"[slides_apply] project: {project}")
    print(f"[slides_apply] {len(pairs)} SVG/MD pair(s){' (check only)' if args.check else ''}")
    print()

    total_applied = 0
    total_missing = 0
    total_warnings = 0
    files_modified = 0

    for svg_path, md_path in pairs:
        slots = parse_slides_md(md_path)
        if not slots:
            print(f"  [skip] {md_path.name}: no slot lines parsed")
            continue

        warn = maybe_warn_on_dest_newer(svg_path, md_path)
        if warn:
            print(warn)
            total_warnings += 1

        original = svg_path.read_text(encoding="utf-8")
        updated, found = apply_slots_to_svg_text(original, slots)

        applied = sum(1 for ok in found.values() if ok)
        missing = [slot for slot, ok in found.items() if not ok]
        total_applied += applied
        total_missing += len(missing)

        if missing:
            for slot in missing:
                print(f"  [warn] {md_path.name}: slot '{slot}' has no <text data-slot=\"{slot}\"> in {svg_path.name}")
                total_warnings += 1

        if updated == original:
            print(f"  [unchanged] {svg_path.name}: no text changes (values already match)")
            continue

        if args.check:
            print(f"  [check] {svg_path.name}: would update {applied} slot(s)")
        else:
            svg_path.write_text(updated, encoding="utf-8")
            files_modified += 1
            # Sync MD mtime to the freshly-written SVG so a subsequent apply
            # does not false-trigger the "SVG newer than MD" warning.
            try:
                new_mtime = svg_path.stat().st_mtime
                os.utime(md_path, (new_mtime, new_mtime))
            except OSError:
                pass
            print(f"  [ok] {svg_path.name}: updated {applied} slot(s)")

    print()
    print(f"[slides_apply] done: {files_modified} SVG file(s) modified, "
          f"{total_applied} slot(s) applied, {total_missing} missing, {total_warnings} warning(s)")

    if args.strict and total_missing > 0:
        print(f"[slides_apply] strict mode: {total_missing} unmatched slot(s); exiting non-zero", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
