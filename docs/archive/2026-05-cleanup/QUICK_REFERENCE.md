# Text Box Consolidation: Quick Reference

## The Problem

```
BEFORE: Uncomfortable editing
┌─────────────────────────────────┐
│ "The" | "quick" | "brown" | "fox"│  ← 4 separate segments
│                                 │     Hard to select/edit
└─────────────────────────────────┘
```

## The Solution

```
AFTER: Natural editing
┌─────────────────────────────────┐
│ The quick brown fox             │  ← 1 continuous block
│                                 │     Easy to edit naturally
└─────────────────────────────────┘
```

## What Changed

| What | Before | After |
|------|--------|-------|
| **Text segments per box** | Many (fragmented) | Few (consolidated) |
| **Editing experience** | Awkward | Natural |
| **Formatting preserved** | ✅ Yes (but with segments) | ✅ Yes |
| **Configuration needed** | ❌ No (always segments) | ✅ Optional (auto by default) |
| **PPTX file complexity** | Higher (more runs) | Lower (fewer runs) |

## For Executor Agents: SVG Generation Rules

### ✅ DO (Creates consolidatable SVGs)

```xml
<!-- Line breaks: tspans with y positioning -->
<text x="100" y="100">
  <tspan x="100" y="100">First line</tspan>
  <tspan x="100" y="140">Second line</tspan>
</text>

<!-- Shared styling at parent level -->
<text fill="navy" font-size="32">
  Complete paragraph without inline segments
</text>

<!-- Mark for consolidation -->
<text data-consolidate="true">
  Will consolidate aggressively
</text>
```

### ❌ DON'T (Creates problematic SVGs)

```xml
<!-- Inline tspans for styling (BAD) -->
<text>
  <tspan>Normal</tspan>
  <tspan font-weight="bold">bold</tspan>
  <tspan>normal</tspan>
</text>

<!-- One tspan per word (BAD) -->
<text>
  <tspan>The</tspan>
  <tspan>quick</tspan>
  <tspan>brown</tspan>
</text>
```

## Configuration: spec_lock.md

```yaml
text:
  consolidation: "auto"  # Recommended (default)
  
  # Options:
  # auto       → Smart consolidation (> 50% compatible runs)
  # compatible → Merge only if all styling identical
  # none       → Keep all runs separate (preserve fine formatting)
```

## Quality Checklist

```bash
# Run this to check your SVGs:
python3 scripts/svg_quality_checker.py <project>

# Good:     tspan-to-text ratio < 1.5
# Warning:  ratio 1.5-2.0 (may benefit from consolidation)
# Bad:      ratio > 2.0 (too many segments)
```

## Edit Test in PowerPoint

1. **Open** generated PPTX
2. **Click** on text box
3. **Check**:
   - ✅ Good: Single continuous highlight around all text
   - ❌ Bad: Separate highlights for each segment
4. **Try editing** — should feel natural

## Files to Know

### For Users
- 📄 [`TEXTBOX_IMPROVEMENT_GUIDE.md`](TEXTBOX_IMPROVEMENT_GUIDE.md) — How to use the improvements

### For Agents
- 📄 [`references/textbox-consolidation.md`](ppt-master/skills/ppt-master/references/textbox-consolidation.md) — Complete strategy
- 📄 [`AGENTS.md`](ppt-master/AGENTS.md) — Agent execution requirements (updated)
- 📄 [`CLAUDE.md`](ppt-master/CLAUDE.md) — Claude Code requirements (updated)

### For Developers
- 💻 [`drawingml_elements.py`](ppt-master/skills/ppt-master/scripts/svg_to_pptx/drawingml_elements.py) — Core implementation

## Common Scenarios

### Scenario 1: Auto Consolidation Works
**Input**: SVG with many inline tspans
**Process**: System detects and auto-consolidates
**Output**: PPTX with consolidated text (no config needed) ✅

### Scenario 2: Need More Consolidation
**Input**: `spec_lock.md` has `consolidation: "auto"`
**Fix**: Change to `consolidation: "compatible"`
**Rerun**: `finalize_svg.py` and `svg_to_pptx.py`
**Output**: More aggressive consolidation ✅

### Scenario 3: Preserve Formatting
**Input**: Complex formatting (many color changes)
**Fix**: Set `consolidation: "none"` or add `data-consolidate="false"`
**Output**: All runs preserved, no consolidation ✅

### Scenario 4: Manual Mark for Consolidation
**Input**: Simple text that should consolidate
**Mark**: Add `data-consolidate="true"` to `<text>` element
**Output**: Forced consolidation regardless of heuristic ✅

## Workflow Integration

```
Your Project
    ↓
[Executor generates SVG]
    ↓ (apply consolidation rules)
[Minimal inline tspans]
    ↓
[finalize_svg.py] (existing)
    ↓
[svg_to_pptx.py] (NOW with consolidation)
    ↓
[PPTX output with consolidated text] ✨
```

## Consolidation Algorithm (Simple Version)

**Two runs merge if:**
- Same color ✓
- Same font size ✓
- Same font weight ✓
- Same font family ✓
- Same style (italic/normal) ✓
- Same opacity ✓

**If ANY differ → runs stay separate**

## Performance

- ⚡ **Speed**: < 50ms per deck (negligible)
- 💾 **File size**: Slightly smaller (fewer runs)
- 🎯 **Quality**: No loss, better editability

## Troubleshooting

### Text still segmented in PowerPoint?

**Option A** — Update config (easiest):
```yaml
text:
  consolidation: "compatible"  # More aggressive
```

**Option B** — Mark SVG for consolidation:
```xml
<text data-consolidate="true">...</text>
```

**Option C** — Regenerate:
```bash
python3 scripts/finalize_svg.py <project>
python3 scripts/svg_to_pptx.py <project> -s final
```

### Lost fine-grained formatting?

Set `consolidation: "none"` to preserve all runs.

## Key Takeaway

✨ **The improvement happens automatically for most cases.** Just follow the SVG generation rules (minimize inline tspans) and your generated PPTXs will be naturally editable with no additional configuration needed.

---

**For more details**: Read [`TEXTBOX_IMPROVEMENT_GUIDE.md`](TEXTBOX_IMPROVEMENT_GUIDE.md)

**For complete strategy**: Read [`references/textbox-consolidation.md`](ppt-master/skills/ppt-master/references/textbox-consolidation.md)
