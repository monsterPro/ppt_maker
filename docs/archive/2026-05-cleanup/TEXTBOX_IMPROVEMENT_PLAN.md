# PPT Generator Text Box Consolidation Improvement Plan

## Problem Analysis

**Issue**: Generated PPTX files have segmented text boxes that are uncomfortable to edit. Each `<tspan>` in SVG becomes a separate **run** in PowerPoint's DrawingML, making text-editing fragmented.

### Current Flow
```
SVG generation (tspans) 
  → flatten_tspan.py (only flattens line breaks, not inline formatting)
  → drawingml_converter.py (each tspan → separate run)
  → PPTX output (multiple runs = segments in same textbox)
```

### Why This Happens
1. `drawingml_elements.py:_collect_tspan_runs()` creates one run per tspan
2. Even inline formatting (bold/italic within text) creates separate tspans
3. Current `flatten_tspan.py` only handles line-break tspans (with y/dy attributes)
4. Inline formatting tspans remain and become separate segments in PPTX

## Solution Strategy

### Level 1: SVG Generation (Agent Guidance)
**Where**: Executor agent (SKILL.md Step 6)
- **Rule**: Use single `<text>` element with **minimal tspans** — only for line breaks, NOT for inline formatting
- **Inline formatting**: Use `<tspan>` only when y/dy/x changes (new line), not for styling
- **Alternative**: Move inline styling to CSS `<style>` or shared `fill` attributes on parent `<text>`

### Level 2: SVG Post-processing (Enhanced flatten_tspan.py)
**Where**: `finalize_svg.py --flatten-text` step
**Improvement**: Add mode for **aggressive consolidation**
- Merge inline tspans (same line, different styling) into single text with run-level styling hints
- Create optional `data-consolidate="true"` markers for PPTX converter
- Output: Simpler SVG with fewer tspan elements

### Level 3: PPTX Conversion (New consolidation logic)
**Where**: `drawingml_elements.py:convert_text()`
**New feature**: Run consolidation
- Option 1: **Merge-on-export** — combine adjacent runs with **compatible styling** during PPTX write
- Option 2: **Single-box mode** — consolidate all runs into single run if formatting is simple
- Add configuration flag: `TEXTBOX_CONSOLIDATION_MODE` (none / compatible / aggressive)

### Level 4: Post-export PPTX Consolidation (New script)
**Where**: New script `consolidate_pptx_runs.py`
- Read final PPTX, merge text runs within each text box
- Preserve styling where possible; drop fine-grained formatting if needed
- Produces PPTX with single merged run per text box

---

## Implementation Phases

### Phase 1: Documentation & Guidance (Quick Win)
- [ ] Add agent guidance to `SKILL.md` Executor section (Step 6)
- [ ] Create `references/textbox-strategy.md` with SVG text generation rules
- [ ] Update `references/executor-base.md` with text layer best practices

### Phase 2: Enhanced SVG Post-processing
- [ ] Extend `flatten_tspan.py` with `--consolidate-inline` mode
- [ ] Integrate into `finalize_svg.py` as new option
- [ ] Test on sample projects

### Phase 3: PPTX Consolidation (Core Fix)
- [ ] Add `consolidate_runs()` method to `drawingml_elements.py`
- [ ] Add config option to `pptx_builder.py`: `consolidate_text_runs=True`
- [ ] Modify `convert_text()` to call consolidation
- [ ] Test with generated PPTXs

### Phase 4: Post-export Safety Valve
- [ ] Create `consolidate_pptx_runs.py` for manual cleanup
- [ ] Add to post-processing pipeline options
- [ ] Document trade-offs

---

## Configuration Options

Add to project `spec_lock.md`:
```yaml
# Text box consolidation strategy
textbox:
  consolidation: "auto"  # auto | none | compatible | aggressive
  preserve_inline_style: true  # keep bold/italic/color if possible
  single_line_collapse: true   # merge single-line text automatically
```

---

## Agent Implementation Checklist

### Strategist Role
- [ ] Review text styling in design spec
- [ ] Flag slides with complex inline formatting that may not consolidate well

### Executor Role  
- [ ] **MUST** use single `<text>` per textbox region
- [ ] Organize tspans by LINE not by STYLE
- [ ] Use CSS or parent attributes for shared styling
- [ ] Document any inline styling that must be preserved

### Quality Checklist
- [ ] Run `svg_quality_checker.py` to flag high tspan count
- [ ] Verify `flatten_tspan.py` output reduces complexity
- [ ] Test PPTX editing experience: open in PowerPoint, try selecting/editing text

---

## Files to Modify

1. **ppt-master/skills/ppt-master/SKILL.md**
   - Step 6 (Executor): Add text generation guidance
   - Step 7.2: Add textbox consolidation option

2. **ppt-master/skills/ppt-master/references/executor-base.md**
   - §4 Visual Construction: Text layer best practices

3. **ppt-master/skills/ppt-master/references/shared-standards.md**
   - Add TEXT LAYER section with tspan guidelines

4. **ppt-master/skills/ppt-master/scripts/svg_to_pptx/drawingml_elements.py**
   - Add `consolidate_runs()` function
   - Modify `convert_text()` to consolidate

5. **ppt-master/skills/ppt-master/scripts/svg_finalize/flatten_tspan.py**
   - Add `--consolidate-inline` mode

6. **ppt-master/AGENTS.md** & **ppt-master/CLAUDE.md**
   - Update with text consolidation workflow

---

## Success Criteria

✅ User can edit text in generated PPTX without seeing segmented runs
✅ Inline formatting (bold/italic/color) preserved when simple
✅ Line breaks work naturally
✅ No loss of layout or positioning
✅ Backward compatible (existing PPTs unaffected)
