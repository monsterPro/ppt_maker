# VisualSol Lecture - Google Style Validation Deck

This project reuses the content from
`../VisualSol_Lecture_ppt169_20260504` and renders a compact six-slide deck in a
different template style.

## Template

- Template family: `google_style`
- Canvas: 1280 x 720, 16:9
- Background: white / light gray
- Accents: Google blue, red, yellow, green
- Typography: Arial

## Validation Goals

- PPTX opens without repair prompts.
- Slide Master exists and has clean reusable layouts.
- Title and section layouts do not inherit content-slide header chrome.
- Content layouts have reusable header/footer structure.
- Placeholder text boxes do not draw visible dashed borders.
- Footer and slide numbers are master-managed.
- Standalone bottom-right page number text in generated SVG is skipped.
- Master does not inherit VisualSol dark radial glows when the new template SVG
  has no radial gradients.

## Slide Outline

1. Cover: 3D Scene Reconstruction & Generation.
2. Agenda: four sections of the lecture.
3. Section Header: What is 3D Reconstruction?
4. Motivation: why the bottleneck is shifting.
5. Key Takeaways: three summary points.
6. Ending: Thank You / Questions.
