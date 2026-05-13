#!/usr/bin/env python3
"""PPT Master - Slides Text Layer: bootstrap data-slot markers in existing SVGs

Walks <project_path>/svg_output/, finds every plain <text> element that does
not yet carry a data-slot attribute, and inserts a positional slot path of
the form `<g_id>.<index>` based on the nearest named ancestor <g id="...">.

Idempotent: <text> elements that already have data-slot are left untouched.

Skipped (no slot added):
- <text> inside <g id="footer">  (footer is auto-content)
- <text> with <tspan> children   (tspans are not currently extractable)
- <text> with no named <g> ancestor receives a fallback slot
  `slide.<index>` by default (see --fallback-gid / --no-fallback)

After running this, run slides_extract.py to populate slides/*.md.

Usage:
    python scripts/slides_init.py <project_path>
    python scripts/slides_init.py <project_path> --check     # report intended writes; do not modify files
    python scripts/slides_init.py <project_path> --skip footer,background,decoration   # skip these g_ids
    python scripts/slides_init.py <project_path> --fallback-gid slide                  # fallback group id (default 'slide')
    python scripts/slides_init.py <project_path> --no-fallback                         # disable fallback (skip orphan texts)
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

DEFAULT_SKIP_GIDS = {"footer"}


def is_text(el: ET.Element) -> bool:
    return el.tag.endswith("}text") or el.tag == "text"


def is_tspan(el: ET.Element) -> bool:
    return el.tag.endswith("}tspan") or el.tag == "tspan"


def is_g(el: ET.Element) -> bool:
    return el.tag.endswith("}g") or el.tag == "g"


def has_tspan_child(el: ET.Element) -> bool:
    return any(is_tspan(child) for child in el)


def build_parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def nearest_named_g(el: ET.Element, parent_map: dict[ET.Element, ET.Element]) -> str | None:
    """Walk up the ancestor chain; return the id of the nearest <g id="..."> ancestor, or None."""
    cur = parent_map.get(el)
    while cur is not None:
        if is_g(cur):
            gid = cur.get("id")
            if gid:
                return gid
        cur = parent_map.get(cur)
    return None


def analyze_svg(
    svg_path: Path,
    skip_gids: set[str],
    fallback_gid: str | None,
) -> tuple[list[str | None], list[str], int, int]:
    """Walk an SVG; return (per_text_slot_or_None, warnings, total_text_count, fallback_count).

    Order of `per_text_slot_or_None` matches ElementTree's document-order iteration
    over <text> elements, which aligns with regex-based discovery in the raw text.

    `fallback_gid`: if not None, orphan <text> (no named <g> ancestor) receives a
    slot under this synthetic group id (e.g., 'slide.1', 'slide.2'). If None,
    orphan texts are skipped with a warning.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    per_text: list[str | None] = []
    warnings: list[str] = []
    counters: dict[str, int] = {}
    total_texts = 0
    fallback_count = 0

    for el in root.iter():
        if not is_text(el):
            continue
        total_texts += 1

        if el.get("data-slot"):
            per_text.append(None)
            continue

        if has_tspan_child(el):
            per_text.append(None)
            warnings.append(f"text containing <tspan> skipped (no slot): \"{(el.text or '').strip()[:40]}\"")
            continue

        gid = nearest_named_g(el, parent_map)
        if gid is None:
            if fallback_gid is None:
                per_text.append(None)
                warnings.append(f"text with no named <g> ancestor skipped: \"{(el.text or '').strip()[:40]}\"")
                continue
            gid = fallback_gid
            fallback_count += 1

        if gid in skip_gids:
            per_text.append(None)
            continue

        idx = counters.get(gid, 0) + 1
        counters[gid] = idx
        per_text.append(f"{gid}.{idx}")

    return per_text, warnings, total_texts, fallback_count


# Match a single <text ...> opening tag. Greedy on attributes, no nested '>'.
TEXT_OPEN_RE = re.compile(r"<text\b([^>]*)>", flags=re.UNICODE)


def insert_slot_attributes(svg_text: str, per_text_slots: list[str | None]) -> tuple[str, int]:
    """Insert data-slot attribute on each <text> opening tag whose slot is not None."""
    chunks: list[str] = []
    last_pos = 0
    inserted = 0
    iter_slots = iter(per_text_slots)

    for m in TEXT_OPEN_RE.finditer(svg_text):
        slot = next(iter_slots, None)
        if slot is None:
            continue
        attrs = m.group(1)
        new_open = f'<text data-slot="{slot}"{attrs}>'
        chunks.append(svg_text[last_pos:m.start()])
        chunks.append(new_open)
        last_pos = m.end()
        inserted += 1

    chunks.append(svg_text[last_pos:])
    return "".join(chunks), inserted


def parse_skip_arg(value: str) -> set[str]:
    items = {item.strip() for item in value.split(",") if item.strip()}
    return items or DEFAULT_SKIP_GIDS


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_path", help="Path to the PPT project directory")
    ap.add_argument("--check", action="store_true", help="Report intended writes; do not modify files")
    ap.add_argument("--skip", default="footer", help="Comma-separated g_ids to skip (default: footer)")
    ap.add_argument("--fallback-gid", default="slide",
                    help="Synthetic group id for orphan texts (no named <g> ancestor); default 'slide'")
    ap.add_argument("--no-fallback", action="store_true",
                    help="Disable fallback group; orphan texts are skipped with a warning")
    args = ap.parse_args()
    fallback_gid: str | None = None if args.no_fallback else (args.fallback_gid or None)

    project = Path(args.project_path).resolve()
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        print(f"Error: svg_output/ not found under {project}", file=sys.stderr)
        return 1

    skip_gids = parse_skip_arg(args.skip)
    svg_files = sorted(svg_dir.glob("*.svg"))
    if not svg_files:
        print(f"Error: no SVG files in {svg_dir}", file=sys.stderr)
        return 1

    print(f"[slides_init] project: {project}")
    print(f"[slides_init] {len(svg_files)} SVG file(s); skip g_ids: {sorted(skip_gids)}")
    print(f"[slides_init] fallback gid for orphan texts: {fallback_gid!r}")
    print(f"[slides_init] mode: {'check' if args.check else 'write'}")
    print()

    total_inserted = 0
    total_fallback = 0
    total_warnings = 0
    files_modified = 0

    for svg_path in svg_files:
        try:
            per_text, warnings, total_text_count, fallback_count = analyze_svg(
                svg_path, skip_gids, fallback_gid,
            )
        except ET.ParseError as e:
            print(f"  [error] {svg_path.name}: parse failed: {e}", file=sys.stderr)
            return 1

        will_insert = sum(1 for s in per_text if s is not None)
        if will_insert == 0:
            print(f"  [skip] {svg_path.name}: nothing to do (already tagged or no eligible text; "
                  f"{total_text_count} <text> total)")
            for w in warnings:
                print(f"          warn: {w}")
                total_warnings += 1
            continue

        original = svg_path.read_text(encoding="utf-8")
        updated, inserted = insert_slot_attributes(original, per_text)

        if inserted != will_insert:
            print(
                f"  [warn] {svg_path.name}: ElementTree expected {will_insert} insertions but regex "
                f"applied {inserted}. The SVG may use multi-line <text> tags or unusual whitespace.",
                file=sys.stderr,
            )

        fallback_note = f", {fallback_count} via fallback '{fallback_gid}'" if fallback_count else ""
        if args.check:
            print(f"  [check] {svg_path.name}: would insert {inserted} data-slot attribute(s){fallback_note}")
        else:
            svg_path.write_text(updated, encoding="utf-8")
            files_modified += 1
            print(f"  [ok] {svg_path.name}: inserted {inserted} data-slot attribute(s){fallback_note}")

        for w in warnings:
            print(f"        warn: {w}")
            total_warnings += 1
        total_inserted += inserted
        total_fallback += fallback_count

    print()
    print(f"[slides_init] done: {files_modified} SVG file(s) modified, "
          f"{total_inserted} attribute(s) inserted "
          f"({total_fallback} via fallback '{fallback_gid}'), {total_warnings} warning(s)")
    if not args.check:
        print("[slides_init] next: python scripts/slides_extract.py <project_path>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
