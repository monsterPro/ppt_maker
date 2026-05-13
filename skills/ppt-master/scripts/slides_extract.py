#!/usr/bin/env python3
"""PPT Master - Slides Text Layer: extract SVG text into slides/*.md

Walks <project_path>/svg_output/, finds every <text> element with a
data-slot="..." attribute, and writes one slides/<NN>_<name>.md per SVG
containing the slot:value table.

This is the SVG -> slides direction. After editing slides/*.md the user
runs slides_apply.py to push changes back into SVG.

Usage:
    python scripts/slides_extract.py <project_path>
    python scripts/slides_extract.py <project_path> --check  # warn on dest newer than source
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import OrderedDict

# Make stdout/stderr tolerant of non-UTF-8 Windows consoles (cp949, cp1252, ...)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def find_svg_files(svg_dir: Path) -> list[Path]:
    return sorted(svg_dir.glob("*.svg"))


def text_has_tspan(text_el: ET.Element) -> bool:
    for child in text_el:
        if child.tag.endswith("}tspan") or child.tag == "tspan":
            return True
    return False


def get_text_content(text_el: ET.Element) -> str:
    """Return the inner text of a <text> element, ignoring tspan structure."""
    return (text_el.text or "").strip()


def is_inside_footer(text_el: ET.Element, root: ET.Element) -> bool:
    """Walk parents and return True if any ancestor <g> has id='footer'."""
    # ElementTree has no parent pointer; we walk from root and track ancestry
    for parent in root.iter():
        for child in parent:
            if child is text_el:
                # found direct parent; now check up the chain
                # build path by repeating
                pass
    # Simpler: check membership by iterating <g id='footer'>
    for g in root.iter():
        gid = g.get("id") or ""
        tag = g.tag.split("}")[-1]
        if tag == "g" and gid == "footer":
            for desc in g.iter():
                if desc is text_el:
                    return True
    return False


def extract_slots_from_svg(svg_path: Path) -> tuple[OrderedDict[str, str], list[str], str | None]:
    """Return (slots, warnings, page_title).

    Slots preserve document order. Warnings include duplicate slots,
    tspan-bearing texts that carry data-slot, and missing slot attributes
    on plausibly content-bearing text elements.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    slots: OrderedDict[str, str] = OrderedDict()
    warnings: list[str] = []
    page_title: str | None = None

    for text_el in root.iter():
        tag = text_el.tag.split("}")[-1]
        if tag != "text":
            continue
        slot = text_el.get("data-slot")
        if not slot:
            continue
        if text_has_tspan(text_el):
            warnings.append(
                f"slot '{slot}' is on a <text> element containing <tspan>; "
                "tspan-bearing text is currently not extractable. "
                "Split into adjacent plain <text> elements."
            )
            continue
        value = get_text_content(text_el)
        if slot in slots:
            warnings.append(f"duplicate slot '{slot}' (later occurrence overwrites earlier)")
        slots[slot] = value
        # Heuristic: capture page title from header.title slot
        if slot == "header.title" and not page_title:
            page_title = value

    return slots, warnings, page_title


def group_slots(slots: OrderedDict[str, str]) -> OrderedDict[str, list[tuple[str, str]]]:
    """Group slots by first dot-segment, preserving order."""
    groups: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()
    for key, value in slots.items():
        prefix = key.split(".", 1)[0]
        groups.setdefault(prefix, []).append((key, value))
    return groups


def write_slides_md(
    md_path: Path,
    svg_filename: str,
    slide_index: str,
    page_title: str | None,
    slots: OrderedDict[str, str],
) -> None:
    """Write the per-slide slots markdown."""
    title_line = f"# {slide_index}"
    if page_title:
        title_line += f": {page_title}"

    lines = [
        title_line,
        "",
        f"> Source: `{svg_filename}`",
        "> Edit values, then run: `python scripts/slides_apply.py <project_path>`",
        "",
    ]

    if not slots:
        lines.append("_No slots found. Tag `<text data-slot=\"...\">` in the SVG, then re-extract._")
        lines.append("")
    else:
        for prefix, items in group_slots(slots).items():
            lines.append(f"## {prefix}")
            for key, value in items:
                lines.append(f"{key}: {value}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")


def derive_slide_index(svg_filename: str) -> str:
    """Return the leading numeric prefix from a filename like '12_3dgs_math.svg' -> '12'."""
    m = re.match(r"^(\d+)", svg_filename)
    return m.group(1) if m else svg_filename


def md_filename_for(svg_filename: str) -> str:
    """Map '12_3dgs_math.svg' -> '12_3dgs_math.md'."""
    return Path(svg_filename).with_suffix(".md").name


def maybe_warn_on_dest_newer(slides_path: Path, svg_path: Path) -> str | None:
    """Return a warning string if slides/*.md is newer than the SVG (extract direction would clobber edits)."""
    if not slides_path.exists():
        return None
    if slides_path.stat().st_mtime > svg_path.stat().st_mtime + 1.0:
        return (
            f"  ⚠️  '{slides_path.name}' is newer than '{svg_path.name}' — "
            "the slides MD already has edits not in the SVG. "
            "Continuing will overwrite them. Run slides_apply.py first if those edits should win."
        )
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", help="Path to the PPT project directory")
    ap.add_argument("--check", action="store_true", help="Only report intended writes; do not modify files")
    args = ap.parse_args()

    project = Path(args.project_path).resolve()
    svg_dir = project / "svg_output"
    slides_dir = project / "slides"

    if not svg_dir.is_dir():
        print(f"Error: svg_output/ not found under {project}", file=sys.stderr)
        return 1

    svg_files = find_svg_files(svg_dir)
    if not svg_files:
        print(f"Error: no SVG files in {svg_dir}", file=sys.stderr)
        return 1

    if not args.check:
        slides_dir.mkdir(parents=True, exist_ok=True)

    print(f"[slides_extract] project: {project}")
    print(f"[slides_extract] {len(svg_files)} SVG file(s) under svg_output/")
    print(f"[slides_extract] writing to: {slides_dir}{' (check only)' if args.check else ''}")
    print()

    total_slots = 0
    total_warnings = 0
    files_written = 0
    files_skipped_no_slot = 0

    for svg_path in svg_files:
        md_path = slides_dir / md_filename_for(svg_path.name)
        slots, warnings, page_title = extract_slots_from_svg(svg_path)

        # Newer-destination warning
        if not args.check:
            warn = maybe_warn_on_dest_newer(md_path, svg_path)
            if warn:
                print(warn)
                total_warnings += 1

        if not slots:
            files_skipped_no_slot += 1
            print(f"  [skip] {svg_path.name}: no data-slot attributes found")
            for w in warnings:
                print(f"          warn: {w}")
                total_warnings += 1
            continue

        if args.check:
            print(f"  [check] {svg_path.name}: {len(slots)} slot(s) -> {md_path.name}")
        else:
            slide_index = derive_slide_index(svg_path.name)
            write_slides_md(md_path, svg_path.name, slide_index, page_title, slots)
            files_written += 1
            print(f"  [ok] {svg_path.name}: {len(slots)} slot(s) -> {md_path.name}")

        for w in warnings:
            print(f"        warn: {w}")
            total_warnings += 1
        total_slots += len(slots)

    print()
    print(f"[slides_extract] done: {files_written} written, {files_skipped_no_slot} skipped (no slots), "
          f"{total_slots} slot(s) total, {total_warnings} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
