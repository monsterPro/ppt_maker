# Text Box Consolidation Strategy

## Overview

When SVGs are converted to PPTX, each `<tspan>` element becomes a separate **run** in PowerPoint's text box. This creates segmented text that is uncomfortable to edit. This document provides guidance for agents and implementations to consolidate text runs and improve editability.

## Problem: Why Text Gets Segmented

### Current Flow
```
Executor generates SVG with tspans
  ↓
flatten_tspan.py processes (only handles line breaks, not inline formatting)
  ↓
drawingml_converter creates text shape with multiple runs (one per tspan)
  ↓
PowerPoint user sees segmented, hard-to-edit text
```

### Root Cause
The `_collect_tspan_runs()` function in `drawingml_elements.py` treats each `<tspan>` as an independent run, even if they're semantically part of the same line with only style differences.

## Solution Layers

### Layer 1: SVG Generation (Executor Agent)

**Golden Rule**: Minimize inline tspans. Use them only for line positioning, not styling.

#### DO ✅
```xml
<!-- Line breaks use tspans with y positioning -->
<text x="100" y="100" font-size="32">
  <tspan x="100" y="100">First line</tspan>
  <tspan x="100" y="140">Second line</tspan>
</text>

<!-- Inline styling shared at parent level -->
<text x="100" y="100" fill="blue" font-weight="bold">
  Complete paragraph in single text element
</text>

<!-- CSS-based inline formatting -->
<text x="100" y="100" style="font-size:32px;">
  <tspan class="highlight">Bold part</tspan> regular part
</text>
```

#### DON'T ❌
```xml
<!-- Inline tspans just for styling (creates segments) -->
<text x="100" y="100">
  <tspan>Normal </tspan>
  <tspan font-weight="bold">bold </tspan>
  <tspan>normal</tspan>
</text>

<!-- One tspan per word -->
<text>
  <tspan>The</tspan>
  <tspan>quick</tspan>
  <tspan>brown</tspan>
  <tspan>fox</tspan>
</text>
```

#### Text Layer Rules (from CLAUDE.md)

1. **Single text element per content region** — Don't split "title" into multiple text elements
2. **Tspans for line breaks only** — Each tspan represents a new line (has y/dy attribute)
3. **Shared styling at parent level** — Use `<text font-size="X">` not `<tspan font-size="X">`
4. **Marker-based editing** — Use `data-slot="..."` markers for post-export text editing via `slides/*.md`

### Layer 2: SVG Post-processing (flatten_tspan.py + finalize_svg.py)

#### Current Behavior
- `flatten_tspan.py` converts line-break tspans into separate `<text>` elements
- Inline tspans (same-line, different styling) are left alone
- Result: PPTX still has multiple runs per text box

#### Enhanced Behavior (Planned)
```bash
# Consolidate inline tspans into single line with style hints
python3 scripts/finalize_svg.py <project> --consolidate-text

# Output: tspans reduced, more merging possible in PPTX conversion
```

**What it does**:
- Merges same-line tspans when styling differences are minor
- Preserves line-break positioning
- Outputs `data-consolidate` hints for PPTX converter

### Layer 3: PPTX Conversion (drawingml_elements.py)

#### Current Behavior
- Each tspan → separate run
- Fine-grained formatting preserved
- Editing experience: segmented, uncomfortable

#### Improved Behavior (Planned)
New configuration flag in `spec_lock.md`:
```yaml
textbox_consolidation: "auto"  # none | compatible | aggressive
  # auto: merge compatible runs, preserve styling
  # compatible: merge if color/font unchanged
  # aggressive: single run, drop fine-grained formatting
```

**Implementation in convert_text()**:
```python
def convert_text(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    # ... existing code ...
    runs = _build_text_runs(elem, parent_attrs)
    
    # NEW: consolidate compatible runs
    if ctx.consolidation_mode == "auto":
        runs = _consolidate_compatible_runs(runs)
    elif ctx.consolidation_mode == "aggressive":
        runs = _consolidate_all_runs(runs)
    
    # ... create shape with consolidated runs ...
```

### Layer 4: Post-export Safety Valve

For PPTXs that still have segmented text after export:
```bash
python3 scripts/consolidate_pptx_runs.py <output.pptx>
```
Opens PPTX, merges text runs, produces `<output>_consolidated.pptx`.

---

## Configuration

### In spec_lock.md
```yaml
# Text box editing experience configuration
text:
  # Consolidation strategy during PPTX export
  consolidation: "auto"  # none | auto | aggressive
  
  # Preserve inline styling (bold/italic/color)?
  preserve_inline_formatting: true
  
  # Single-run mode (all text in one segment)?
  single_run_mode: false
```

### Per-slide in SVG Data Attributes
```xml
<text data-consolidate="true" data-preserve-style="true">
  <!-- Hints to PPTX converter -->
</text>

<text data-bullet="true" data-bullet-level="0">
  Native PowerPoint bullet item
</text>
```

`data-bullet="true"` creates a real PowerPoint bullet paragraph during PPTX
conversion. Literal prefixes such as `• item`, `- item`, and `* item` are also
converted to native bullets with the visible prefix removed. Use this only for
semantic lists, not for every body text line.

---

## Agent Responsibilities

### Strategist
- [ ] Review design spec for text styling complexity
- [ ] Flag slides where fine-grained inline formatting is critical
- [ ] Recommend consolidation mode based on design needs

### Executor
- [ ] Generate SVG with **minimal inline tspans**
- [ ] Use tspans **only for line breaks** (y/dy attributes)
- [ ] Share styling at parent `<text>` level when possible
- [ ] Add `data-consolidate="true"` markers for simple text boxes
- [ ] Test: Run `svg_quality_checker.py` to verify tspan efficiency

### Quality Gate
- [ ] `svg_quality_checker.py` checks tspan-to-text ratio
- [ ] Warning if ratio > 1.5 (more than 1.5 tspans per text element on average)
- [ ] Flag high-complexity inline formatting for manual review

---

## Editing Workflow After Export

### If text still has segments in PowerPoint:

**Option A: Live editing** (fastest)
- Select text box
- Edit directly in PowerPoint
- Segments become a single unified text on first edit

**Option B: Re-export with aggressive consolidation**
```bash
# Update spec_lock.md
text:
  consolidation: "aggressive"

# Re-run post-processing
python3 scripts/finalize_svg.py <project>
python3 scripts/svg_to_pptx.py <project> -s final
```

**Option C: Post-export consolidation tool** (safest)
```bash
# Merge runs without regenerating SVG
python3 scripts/consolidate_pptx_runs.py <output.pptx> -o <output>_merged.pptx
```

---

## Implementation Timeline

| Phase | Component | Status | Owner |
|-------|-----------|--------|-------|
| 1 | Agent guidance (this doc + SKILL.md) | ✅ Ready | Documentation |
| 2 | `flatten_tspan.py --consolidate-inline` | 🔄 Planned | Dev |
| 3 | PPTX run consolidation in `drawingml_elements.py` | 🔄 Planned | Dev |
| 4 | `consolidate_pptx_runs.py` post-export tool | 🔄 Planned | Dev |
| 5 | Integration tests and examples | 🔄 Planned | QA |

---

## FAQ

**Q: Will consolidation break my formatting?**
A: "auto" mode preserves formatting when possible. Use "aggressive" only if editing comfort matters more than styling precision.

**Q: Can I edit consolidated text in PowerPoint?**
A: Yes, fully. No difference in functionality—just one continuous text box instead of segments.

**Q: What if I NEED fine-grained inline styling?**
A: Set `consolidation: "none"` in spec_lock.md. Or set `preserve_inline_formatting: true` to keep style info but still merge runs visually.

**Q: Does this affect my SVG exports or charts?**
A: No. Consolidation happens only during PPTX conversion. SVGs are unchanged.
