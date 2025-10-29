from __future__ import annotations

from pathlib import Path

import click

from ..exporters.csv_exporter import (
    ColumnMode,
    export_splits_to_csv,
    export_to_csv,
)
from ..logger import setup_logger


@click.command(name="export-csv")
@click.option(
    "--input",
    "input_path",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Input JSONL file or directory containing train/val/test.jsonl",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Output CSV file path (or directory if --split is used)",
)
@click.option(
    "--mode",
    type=click.Choice(["basic", "detailed", "full"], case_sensitive=False),
    default="detailed",
    help="Column configuration mode",
)
@click.option(
    "--split",
    is_flag=True,
    help="Export as separate CSVs (train.csv, val.csv, test.csv)",
)
@click.option(
    "--encoding",
    type=click.Choice(["utf-8", "utf-8-sig"]),
    default="utf-8",
    help="File encoding (utf-8-sig for Excel compatibility)",
)
@click.option(
    "--delimiter",
    type=click.Choice([",", "\t", ";"]),
    default=",",
    help="CSV delimiter",
)
@click.option(
    "--include-index",
    is_flag=True,
    help="Include row numbers",
)
def export_csv_cmd(
    input_path: Path,
    output_path: Path,
    mode: str,
    split: bool,
    encoding: str,
    delimiter: str,
    include_index: bool,
) -> None:
    """Export dataset to CSV format."""
    setup_logger()

    column_mode = ColumnMode(mode.lower())

    if split:
        # Export splits separately
        export_splits_to_csv(
            input_dir=input_path,
            output_dir=output_path,
            mode=column_mode,
            encoding=encoding,
            delimiter=delimiter,
            include_index=include_index,
        )
        click.echo(f"✓ Exported splits to {output_path}")
    else:
        # Export single file
        export_to_csv(
            input_path=input_path,
            output_path=output_path,
            mode=column_mode,
            encoding=encoding,
            delimiter=delimiter,
            include_index=include_index,
        )
        click.echo(f"✓ Exported CSV to {output_path}")

