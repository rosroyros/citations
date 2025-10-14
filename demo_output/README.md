# Layout Demos

This directory contains visual demos of both page layout types.

## Files

- **`index.html`** - Start here! Index page with links to both demos
- **`demo_source_type.html`** - Source Type layout (single-column, 900px)
- **`demo_mega_guide.html`** - Mega Guide layout (two-column with sidebar, 1200px)

## How to View

1. Open `index.html` in your browser
2. Or run: `open index.html`

## Compare With Mockups

These demos match the approved mockups:
- **Source Type:** `design/mocks/source_type_mockup.html`
- **Mega Guide:** `design/mocks/mega_guide_mockup.html`

## Features Demonstrated

### Source Type Layout
✅ Single-column (900px)
✅ No sidebar
✅ Related resources grid at bottom
✅ Dark footer (#1f2937)
✅ Purple branding (#9333ea)

### Mega Guide Layout
✅ Two-column (1200px + 300px sidebar)
✅ Sidebar with related guides
✅ Sidebar with page info (word count, reading time)
✅ Dark footer (#1f2937)
✅ Purple branding (#9333ea)

Both layouts are fully responsive and collapse appropriately on mobile devices (768px breakpoint).

## Regenerating Demos

To regenerate these demos with updated content:

```bash
python3 generate_demo.py
```

The script is located in the project root.
