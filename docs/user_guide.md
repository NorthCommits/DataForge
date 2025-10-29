# DataForge User Guide

Complete guide to using DataForge for dataset creation and curation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [CSV Export Guide](#csv-export-guide)
3. [Use Cases](#use-cases)
4. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation and Setup

See the main [README.md](../README.md) for installation instructions.

### Basic Workflow

```bash
# 1. Scrape content
python -m dataforge.cli.main scrape-tavily --topic "your topic" --limit 50

# 2. Process and clean
python -m dataforge.cli.main process --input ./data/raw/*.jsonl --output ./datasets/my_dataset

# 3. Export to CSV
python -m dataforge.cli.main export-csv --input ./datasets/my_dataset --output ./datasets/my_dataset.csv --split
```

## CSV Export Guide

### Overview

DataForge provides flexible CSV export functionality with multiple column configurations, encoding options, and formatting choices. CSV export is ideal for:

- Excel/Google Sheets analysis
- Spreadsheet-based workflows
- Sharing datasets with non-technical team members
- Quick data inspection
- Integration with traditional BI tools

### Column Modes

#### Basic Mode

Includes only essential fields:
- `url`: Source URL
- `title`: Document title
- `content`: Main text content

**Use Case**: Quick export for simple analysis or when file size is a concern.

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset/train.jsonl \
  --output ./datasets/my_dataset/train.csv \
  --mode basic
```

#### Detailed Mode (Default)

Includes core fields plus quality metrics:
- `url`: Source URL
- `title`: Document title
- `content`: Main text content
- `score`: Source credibility score
- `source`: Extracted domain name

**Use Case**: Most common use case, provides good balance of information and file size.

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./datasets/my_dataset \
  --mode detailed \
  --split
```

#### Full Mode

Includes all available fields:
- All fields from detailed mode
- `scraped_at`: Timestamp when content was scraped
- Additional metadata fields
- Flattened nested JSON structures

**Use Case**: Complete data export for comprehensive analysis or archival purposes.

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./datasets/my_dataset_full.csv \
  --mode full
```

### Export Options

#### Single File vs. Split Files

**Single File Export:**
```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset/train.jsonl \
  --output ./datasets/my_dataset/train.csv
```

**Split Export (Recommended for train/val/test):**
```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./datasets/my_dataset_csv \
  --split
```
This creates: `train.csv`, `val.csv`, `test.csv`

#### Excel Compatibility

For Excel compatibility, use UTF-8 BOM encoding:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./datasets/my_dataset \
  --encoding utf-8-sig \
  --split
```

#### Custom Delimiters

**Comma (default):**
```bash
--delimiter ","
```

**Tab-separated:**
```bash
--delimiter "\t"
```

**Semicolon (common in European locales):**
```bash
--delimiter ";"
```

#### Including Row Numbers

Add an index column for easier reference:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset/train.jsonl \
  --output ./datasets/my_dataset/train.csv \
  --include-index
```

### Automated CSV Export During Processing

Export CSV files automatically during dataset processing:

```bash
python -m dataforge.cli.main process \
  --input ./data/raw/tavily_topic_2025-10-28.jsonl \
  --output ./datasets/my_dataset \
  --export-csv \
  --csv-mode detailed
```

This creates both JSONL and CSV files in the output directory.

### Python API Usage

You can also use the CSV exporter programmatically:

```python
from dataforge.exporters.csv_exporter import (
    ColumnMode,
    export_to_csv,
    export_splits_to_csv,
)
from pathlib import Path

# Export single file
export_to_csv(
    Path("dataset/train.jsonl"),
    Path("dataset/train.csv"),
    mode=ColumnMode.DETAILED,
    encoding="utf-8-sig",
    include_index=False,
)

# Export splits
export_splits_to_csv(
    Path("dataset"),
    Path("csv_output"),
    mode=ColumnMode.FULL,
    encoding="utf-8",
    delimiter=",",
    include_index=True,
)
```

## Use Cases

### 1. Dataset Review and Quality Control

Export to CSV for manual review of dataset quality:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./review/dataset_review.csv \
  --mode detailed \
  --split
```

Then open in Excel/Google Sheets to:
- Review sample documents
- Check quality scores
- Identify problematic entries
- Share findings with team

### 2. Statistical Analysis

Export with full mode for comprehensive analysis:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./analysis/full_data.csv \
  --mode full
```

Use with pandas, R, or Excel for:
- Descriptive statistics
- Quality score distributions
- Source diversity analysis
- Temporal trends (if timestamps available)

### 3. Collaboration with Non-Technical Teams

Export CSV files for team members who prefer spreadsheets:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset \
  --output ./shared/dataset_export \
  --mode detailed \
  --encoding utf-8-sig \
  --split
```

### 4. Integration with Traditional Tools

Export for use with legacy systems or tools that don't support JSONL:

```bash
python -m dataforge.cli.main export-csv \
  --input ./datasets/my_dataset/train.jsonl \
  --output ./export/train.csv \
  --mode basic \
  --delimiter "\t"
```

## Troubleshooting

### Common Issues

#### Issue: CSV file appears corrupted in Excel

**Solution**: Use UTF-8 BOM encoding:
```bash
--encoding utf-8-sig
```

#### Issue: Special characters not displaying correctly

**Solution**: Ensure UTF-8 encoding and that your text editor/viewer supports UTF-8. For Excel, always use `utf-8-sig`.

#### Issue: Large files causing memory errors

**Solution**: 
- Use basic or detailed mode instead of full mode
- Process splits separately instead of all at once
- Consider streaming for very large datasets (see Python API)

#### Issue: Nested JSON not appearing in CSV

**Solution**: Nested structures are automatically flattened with underscore separators (e.g., `metadata_author_name`). Use full mode to ensure all nested fields are included.

#### Issue: CSV file not found after export

**Solution**: 
- Check that the output directory path exists or is writable
- Verify input file/directory path is correct
- Check file permissions

#### Issue: Empty CSV file

**Possible Causes**:
- Input JSONL file is empty or contains no valid records
- All records were filtered out during processing
- File encoding issues preventing proper reading

**Solution**: 
- Verify input file has data: `wc -l input.jsonl`
- Check for JSON parsing errors in logs
- Try re-processing the raw data

### Performance Tips

1. **Use Basic Mode for Large Datasets**: Reduces memory usage and file size
2. **Export Splits Separately**: Process one split at a time for very large datasets
3. **Avoid Full Mode Unless Needed**: Full mode includes all metadata, significantly increasing file size
4. **Use Tab Delimiters**: Faster processing for very large files (slightly)

### Best Practices

1. **Always validate exports**: Check a few rows manually to ensure data integrity
2. **Use UTF-8-sig for Excel**: Prevents encoding issues when sharing with Excel users
3. **Keep original JSONL files**: CSV is a lossy format for nested data; preserve originals
4. **Document column meanings**: Share column definitions with your team
5. **Version control datasets**: Track dataset versions alongside code changes

## Advanced Usage

### Custom Column Selection

If you need custom column selection, you can extend the exporter:

```python
from dataforge.exporters.csv_exporter import export_to_csv, ColumnMode
from pathlib import Path
import pandas as pd
import json

# Load data
with Path("dataset/train.jsonl").open() as f:
    records = [json.loads(line) for line in f]

# Custom selection
custom_data = [
    {
        "title": r["title"],
        "url": r["url"],
        "word_count": len(r.get("content", "").split()),
    }
    for r in records
]

# Save
df = pd.DataFrame(custom_data)
df.to_csv("custom.csv", index=False)
```

### Streaming Large Files

For very large files, use streaming:

```python
from dataforge.cli.process import _iter_jsonl
from pathlib import Path
import csv

input_path = Path("large_dataset.jsonl")
output_path = Path("large_dataset.csv")

with output_path.open("w", encoding="utf-8", newline="") as f:
    writer = None
    for record in _iter_jsonl(input_path):
        if writer is None:
            writer = csv.DictWriter(f, fieldnames=record.keys())
            writer.writeheader()
        writer.writerow(record)
```

---

For more information, see the [main README](../README.md) or [API documentation](api_reference.md).
