# Citation Input Tool

A standalone HTML tool with rich text editing for manually inputting citations and saving them to JSON format.

## Features

- **Rich Text Editor**: Maintains formatting (italics, bold, underline) when pasting citations
- **Citation Type Selector**: Choose from journal article, book, book chapter, webpage, or social media
- **Markdown Conversion**: Automatically converts italics to underscore markdown format on save
- **JSON Export**: Saves citations in the same JSON format as your existing dataset
- **Progress Tracking**: Shows count of saved citations
- **Success/Failure Notifications**: Clear feedback for each submission

## Quick Start

1. **Start the server**:
   ```bash
   python3 citation_server.py
   ```

   Or specify a different port:
   ```bash
   python3 citation_server.py --port 8080
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000` (or your specified port)

3. **Add citations**:
   - Select the citation type from the dropdown
   - Paste your formatted citation in the text area (italics will be preserved)
   - Click "Save Citation"

4. **Check output**:
   Citations are saved to `citations.json` in the current directory

## Usage Details

### Rich Text Editing
- Use the toolbar buttons to format text (italic, bold, underline)
- Paste formatted text directly - italics and other formatting will be preserved
- The editor automatically converts HTML to markdown on save (italics → underscores)

### Citation Types Supported
- Journal Article
- Book
- Book Chapter
- Webpage
- Social Media

### JSON Output Format
Each saved citation follows this format:
```json
{
  "citation_id": "manual_1234567890",
  "citation_text": "Author, A. (2023). _Title of work_. Publisher.",
  "source_type": "book",
  "is_valid": true,
  "metadata": {
    "source": "Manual Input",
    "date_collected": "2025-01-01T12:00:00.000Z",
    "formatting_preserved": true,
    "verified_against_kb": false
  }
}
```

### Server Options
```bash
# Default usage (port 8000, current directory)
python3 citation_server.py

# Custom port
python3 citation_server.py --port 9000

# Custom output directory
python3 citation_server.py --output-dir ./my_citations
```

## Example Workflow

1. Start the server: `python3 citation_server.py`
2. Open `http://localhost:8000` in your browser
3. Select "Journal Article" from the dropdown
4. Paste this formatted citation: `Smith, J. (2023). _The impact of AI on research_. _Journal of Technology_, 15(2), 45-67.`
5. Click "Save Citation"
6. The citation is saved to `citations.json` with italics converted to underscores
7. The form resets automatically for the next citation

## File Structure

```
citations/
├── citation_input.html      # HTML interface
├── citation_server.py       # Python backend server
├── citations.json          # Output file (created automatically)
└── README_CITATION_TOOL.md  # This file
```

## Notes

- The server saves citations in JSONL format (one JSON object per line)
- Each citation gets a unique ID with timestamp
- The tool maintains all existing citation fields for compatibility
- Formatting is preserved in the metadata but converted to markdown for the citation text
- The server runs locally and doesn't require external dependencies