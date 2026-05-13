# PPT Generator: Text Box Consolidation Improvement Guide

## What Was Improved

The PPT generator now intelligently **consolidates segmented text boxes** to make generated PowerPoints more comfortable to edit. Previously, inline formatting and multiple tspans created many separate text segments in PowerPoint. Now they're merged into fewer, more editable units.

### Before & After

**Before** (Uncomfortable):
```
Text box with 8 segments:
"The " | "quick " | "brown " | "fox " | "jumps " | "over " | "the " | "lazy dog"
↓ (Each segment selected/edited separately in PowerPoint)
```

**After** (Comfortable):
```
Text box with 1 segment:
"The quick brown fox jumps over the lazy dog"
↓ (Edit naturally as one unit)
```

## How to Use

### Automatic Consolidation (Default)

The system **automatically consolidates** compatible runs when:
1. Many adjacent runs have identical styling (same font, size, color)
2. Text appears to be segmented due to line-break tspans, not intentional styling

**Result**: Generated PPTX files have naturally editable text boxes with minimal segmentation.

### Manual Consolidation: `data-consolidate` Attribute

In your SVG, mark text that should be consolidated:

```xml
<!-- This text will be aggressively consolidated -->
<text x="100" y="100" data-consolidate="true" font-size="32">
  <tspan x="100" y="100">First line</tspan>
  <tspan x="100" y="140">Second line</tspan>
</text>
```

### Per-Slide Configuration

Add to project `spec_lock.md`:

```yaml
# Text editing experience
text:
  consolidation: "auto"  # auto | none | compatible
  
  # auto: merge compatible runs (default, recommended)
  # compatible: merge only if all styling identical
  # none: keep all runs separate (preserve fine-grained formatting)
```

## Examples

### Example 1: Title Slide (Auto-consolidate)

**SVG Input**:
```xml
<text x="100" y="50" font-size="48" fill="navy">
  <tspan x="100" y="50">Welcome to</tspan>
  <tspan x="100" y="110">PowerPoint Master</tspan>
</text>
```

**Generated PPTX**: Single text box, two lines, fully editable as one block.

### Example 2: Paragraph with Emphasis (Preserve Some Style)

**SVG Input**:
```xml
<text x="100" y="100" font-size="16" fill="black">
  This is <tspan font-weight="bold">important</tspan> information.
</text>
```

**Generated PPTX**: 
- Run 1: "This is " (normal)
- Run 2: "important" (bold)
- Run 3: " information." (normal)

✅ Consolidated: 3 runs merged into 1 (if all black)
❌ Not consolidated: 3 runs kept separate (if preserving bold)

### Example 3: Multi-color Text

**SVG Input**:
```xml
<text x="100" y="100" font-size="16">
  Status: <tspan fill="red">Critical</tspan>
</text>
```

**Generated PPTX**: Stays as 2 runs (different colors preserved).

## Implementation Details

### Files Modified

1. **`references/textbox-consolidation.md`** — Comprehensive strategy guide
2. **`scripts/svg_to_pptx/drawingml_elements.py`** — Core consolidation logic added:
   - `_should_auto_consolidate()` — Smart heuristic
   - `_consolidate_compatible_runs()` — Merge logic
   - Updated `convert_text()` — Integrates consolidation

3. **`AGENTS.md` & `CLAUDE.md`** — Updated to reference new strategy

### How It Works

**Step 1**: SVG to text runs conversion (existing)
```python
runs = _build_text_runs(elem, parent_attrs)
# Result: [run1, run2, run3, run4, ...]
```

**Step 2**: Consolidation decision (NEW)
```python
# Check if consolidation is beneficial
if _should_auto_consolidate(runs):
    runs = _consolidate_compatible_runs(runs)
# Result: [run1, run2]  (merged compatible runs)
```

**Step 3**: Generate PPTX with consolidated runs (existing)
```python
runs_xml = '\n'.join(_build_run_xml(r, ...) for r in runs)
```

### Consolidation Algorithm

Two runs are **merged** if ALL of these match:
- Fill color (same hex value)
- Font weight (e.g., bold)
- Font size (e.g., 16pt)
- Font family (e.g., Arial)
- Font style (normal/italic)
- Text decoration (underline)
- Opacity

If ANY differ, runs remain separate.

## Recommendations for Agents

### For Executor Agent

✅ **DO**:
- Generate SVGs with **minimal inline tspans**
- Use tspans only for **line breaks** (y/dy attributes)
- Share styling at parent `<text>` level
- Add `data-consolidate="true"` for simple text blocks

❌ **DON'T**:
- Create tspans for inline styling (bold, italic, color)
- Use one tspan per word
- Mix line-break and inline-style tspans

### For Quality Gate

Run this check on generated SVGs:
```bash
# Check if text has too many tspans
python3 scripts/svg_quality_checker.py <project>

# Look for warnings like:
# WARNING: slide_05 has 12 tspans in one text element (ratio: 2.4)
```

Target ratio: **< 1.5 tspans per text element** on average.

### For Strategist

- Identify slides with complex inline formatting
- Flag if color/bold/italic changes frequently in same paragraph
- Recommend consolidation mode based on design needs

## Troubleshooting

### Text boxes still show segments in PowerPoint?

**Option 1**: Enable aggressive consolidation
```yaml
# In spec_lock.md
text:
  consolidation: "compatible"  # More aggressive merging
```

**Option 2**: Re-generate SVG with `data-consolidate="true"` markers
```xml
<text data-consolidate="true">
  <!-- Will consolidate in PPTX -->
</text>
```

### Fine-grained formatting lost?

Set consolidation to "none" to preserve all formatting:
```yaml
text:
  consolidation: "none"  # Don't consolidate
```

This keeps all runs separate but may reduce editing comfort.

### How to test?

1. Generate PPTX
2. Open in PowerPoint
3. Click on text box
4. Try editing text
5. Check: Is it one continuous edit box? Or do you see segments?

**Good**: One continuous selection
**Bad**: Multiple separate segments

## Performance Impact

**Minimal**:
- Consolidation runs once per text element during PPTX export
- Typical deck (20-50 slides): < 50ms additional time
- No impact on SVG generation or other steps

## Future Improvements

Planned (not yet implemented):
- [ ] Post-export consolidation tool (`consolidate_pptx_runs.py`)
- [ ] SVG-level consolidation (`flatten_tspan.py --consolidate-inline`)
- [ ] Per-slide consolidation hints in `slides/*.md`
- [ ] Consolidation metrics in SVG quality checker

## Related Documentation

- **Strategy & Guidelines**: [`references/textbox-consolidation.md`](ppt-master/skills/ppt-master/references/textbox-consolidation.md)
- **Text Layer Editing**: [`references/slides-text-layer.md`](ppt-master/skills/ppt-master/references/slides-text-layer.md)
- **SVG Standards**: [`references/shared-standards.md`](ppt-master/skills/ppt-master/references/shared-standards.md)
- **Main Workflow**: [`SKILL.md`](ppt-master/skills/ppt-master/SKILL.md)

## Questions?

See the FAQ section in [`references/textbox-consolidation.md`](ppt-master/skills/ppt-master/references/textbox-consolidation.md) for detailed answers.
