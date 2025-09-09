# JSON to Excel/CSV Converter for Document Intelligence

This tool converts JSON document matching results into structured Excel or CSV format for better readability and analysis.

## Features

- Converts JSON document matching data to Excel (.xlsx) or CSV format
- Automatically formats the output with proper headers
- Handles missing documents (shows "NICHT GEFUNDEN")
- Auto-adjusts column widths in Excel format
- Command-line interface for easy usage

## Installation

Install required dependencies:

```bash
pip3 install pandas openpyxl
```

## Usage

### Command Line

```bash
# Convert to Excel format (default)
python3 json_to_excel_converter.py matcha.Entrümpelung.Alpenglanz.json

# Convert to Excel format (explicit)
python3 json_to_excel_converter.py matcha.Entrümpelung.Alpenglanz.json --format xlsx

# Convert to CSV format
python3 json_to_excel_converter.py matcha.Entrümpelung.Alpenglanz.json --format csv
```

### Programmatic Usage

```python
from json_to_excel_converter import convert_json_to_table

# Convert to Excel
excel_file = convert_json_to_table('input.json', 'xlsx')
print(f"Excel file created: {excel_file}")

# Convert to CSV
csv_file = convert_json_to_table('input.json', 'csv')
print(f"CSV file created: {csv_file}")
```

## Output Format

The converter creates a hierarchical structured table with the following columns:

| Typ                  | Nr  | Bezeichnung   | Beilage           | Beschreibung         | Dateiname            | Begründung      |
| -------------------- | --- | ------------- | ----------------- | -------------------- | -------------------- | --------------- |
| Gefordertes Dokument | 1   | Document name | Attachment number | Document description |                      |                 |
| Bieterdokument       |     |               |                   |                      | Matched filename     | Matching reason |
| Bieterdokument       |     |               |                   |                      | Another matched file | Another reason  |

### Structure:

- **Gefordertes Dokument** rows contain the required document information with a counter
- **Bieterdokument** rows (indented) contain the matched bidder documents for each required document
- **Unzuordenbare Dokumente** section lists documents that couldn't be matched to any required document

### Excel Format Features

- Header information (Ausschreibung, Bieter) at the top
- Auto-adjusted column widths
- Professional formatting
- Single worksheet named "Dokumentenmatching"

### CSV Format Features

- Header information at the top of the file
- UTF-8 encoding for proper character support
- Standard CSV format compatible with Excel and other tools

## Input JSON Structure

The tool expects JSON files with the following structure:

```json
{
  "metadata": {
    "ausschreibung": "Project Name",
    "bieter": "Bidder Name"
  },
  "matched_documents": [
    {
      "gefordertes_doc": {
        "bezeichnung": "Document Name",
        "beilage_nummer": "Attachment Number",
        "beschreibung": "Document Description",
        "matches": [
          {
            "Dateiname": "filename.pdf",
            "Begründung": "Matching reason"
          }
        ]
      }
    }
  ]
}
```

## Example

See `example_usage.py` for a complete example of how to use the converter programmatically.

## Error Handling

- Missing input files are detected and reported
- JSON parsing errors are caught and displayed
- Missing required fields are handled gracefully
- Documents without matches are marked as "NICHT GEFUNDEN"

## Output Files

Output files are named using the pattern: `{ausschreibung}.{bieter}.{format}`

Example: `Entrümpelung.Alpenglanz.xlsx`
