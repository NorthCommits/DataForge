from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger
from tqdm import tqdm


class ColumnMode(str, Enum):
    """Column configuration modes for CSV export."""

    BASIC = "basic"
    DETAILED = "detailed"
    FULL = "full"


def _flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flatten nested dictionary structure."""
    items: List[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(_flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            items.append((new_key, json.dumps(value, ensure_ascii=False)))
        else:
            items.append((new_key, value))
    return dict(items)


def _select_columns(
    record: Dict[str, Any], mode: ColumnMode
) -> Dict[str, Any]:
    """Select columns based on mode configuration."""
    flattened = _flatten_dict(record)

    if mode == ColumnMode.BASIC:
        return {
            "url": record.get("url", ""),
            "title": record.get("title", ""),
            "content": record.get("content", ""),
        }
    elif mode == ColumnMode.DETAILED:
        return {
            "url": record.get("url", ""),
            "title": record.get("title", ""),
            "content": record.get("content", ""),
            "score": record.get("score"),
            "source": record.get("url", "").split("/")[2] if record.get("url") else "",
        }
    else:  # FULL
        # Include all fields, with flattened nested structures
        result = {
            "url": record.get("url", ""),
            "title": record.get("title", ""),
            "content": record.get("content", ""),
            "score": record.get("score"),
            "scraped_at": record.get("scraped_at", ""),
            "source": record.get("url", "").split("/")[2] if record.get("url") else "",
        }
        # Add any additional fields
        for key, value in record.items():
            if key not in result:
                result[key] = value
        return result


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL file and return list of records."""
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON at line {line_num} in {path}: {e}")
    except Exception as e:
        logger.error(f"Error reading JSONL file {path}: {e}")
        raise
    return records


def export_to_csv(
    input_path: Path,
    output_path: Path,
    mode: ColumnMode = ColumnMode.DETAILED,
    encoding: str = "utf-8",
    delimiter: str = ",",
    include_index: bool = False,
    progress: bool = True,
) -> None:
    """
    Export JSONL file to CSV format.

    Args:
        input_path: Path to input JSONL file
        output_path: Path to output CSV file
        mode: Column configuration mode
        encoding: File encoding (utf-8 or utf-8-sig for Excel)
        delimiter: CSV delimiter
        include_index: Whether to include row indices
        progress: Show progress bar
    """
    logger.info(f"Exporting {input_path} to CSV with mode={mode.value}")

    # Read JSONL records
    records = _read_jsonl(input_path)

    if not records:
        logger.warning(f"No records found in {input_path}")
        return

    # Select columns based on mode
    selected_records = [
        _select_columns(record, mode) for record in tqdm(records, disable=not progress, desc="Processing records")
    ]

    # Create DataFrame
    df = pd.DataFrame(selected_records)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to CSV
    try:
        df.to_csv(
            output_path,
            index=include_index,
            encoding=encoding,
            sep=delimiter,
            escapechar="\\" if delimiter == "," else None,
            quotechar='"',
            doublequote=True,
            lineterminator="\n",
        )
        logger.info(f"Successfully exported {len(df)} records to {output_path}")
    except Exception as e:
        logger.error(f"Error writing CSV file {output_path}: {e}")
        raise


def export_splits_to_csv(
    input_dir: Path,
    output_dir: Path,
    mode: ColumnMode = ColumnMode.DETAILED,
    encoding: str = "utf-8",
    delimiter: str = ",",
    include_index: bool = False,
) -> None:
    """
    Export train/val/test splits from directory to separate CSV files.

    Args:
        input_dir: Directory containing train.jsonl, val.jsonl, test.jsonl
        output_dir: Output directory for CSV files
        mode: Column configuration mode
        encoding: File encoding
        delimiter: CSV delimiter
        include_index: Whether to include row indices
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    splits = ["train", "val", "test"]
    for split in splits:
        input_file = input_dir / f"{split}.jsonl"
        if not input_file.exists():
            logger.warning(f"Split file {input_file} not found, skipping")
            continue

        output_file = output_dir / f"{split}.csv"
        export_to_csv(
            input_file,
            output_file,
            mode=mode,
            encoding=encoding,
            delimiter=delimiter,
            include_index=include_index,
            progress=False,
        )

    logger.info(f"Exported splits to {output_dir}")


