from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest

from dataforge.exporters.csv_exporter import (
    ColumnMode,
    export_splits_to_csv,
    export_to_csv,
)


@pytest.fixture
def sample_jsonl_file(tmp_path: Path) -> Path:
    """Create a sample JSONL file for testing."""
    file_path = tmp_path / "test.jsonl"
    records = [
        {
            "url": "https://example.com/article1",
            "title": "Test Article 1",
            "content": "This is the content of article 1 with some text.",
            "score": 0.85,
            "scraped_at": "2025-01-01T10:00:00",
        },
        {
            "url": "https://example.org/article2",
            "title": "Test Article 2",
            "content": "Content with special chars: \"quotes\", newlines\nand tabs\t.",
            "score": 0.92,
        },
        {
            "url": "https://test.com/page",
            "title": "Article 3",
            "content": "Short",
            "score": None,
        },
    ]
    with file_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return file_path


@pytest.fixture
def sample_dataset_dir(tmp_path: Path) -> Path:
    """Create a sample dataset directory with train/val/test splits."""
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    for split in ["train", "val", "test"]:
        file_path = dataset_dir / f"{split}.jsonl"
        records = [
            {
                "url": f"https://example.com/{split}_{i}",
                "title": f"{split.title()} Article {i}",
                "content": f"Content for {split} article {i}",
                "score": 0.8 + i * 0.05,
            }
            for i in range(3)
        ]
        with file_path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    return dataset_dir


def test_export_basic_mode(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with basic column mode."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.BASIC,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert set(rows[0].keys()) == {"url", "title", "content"}


def test_export_detailed_mode(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with detailed column mode."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert "score" in rows[0].keys()
        assert "source" in rows[0].keys()


def test_export_full_mode(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with full column mode."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.FULL,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert "scraped_at" in rows[0].keys()


def test_export_with_index(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with row indices."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        include_index=True,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        # First column should be index (unnamed)
        assert header[0] != "url"


def test_export_special_characters(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export handles special characters correctly."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        content = f.read()
        # Should contain the special characters
        assert "quotes" in content


def test_export_utf8_encoding(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with UTF-8 encoding."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        encoding="utf-8",
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        content = f.read()
        assert content


def test_export_utf8_sig_encoding(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with UTF-8-BOM encoding for Excel compatibility."""
    output_file = tmp_path / "output.csv"
    export_to_csv(
        sample_jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        encoding="utf-8-sig",
        progress=False,
    )

    assert output_file.exists()

    # Check for BOM
    with output_file.open("rb") as f:
        content = f.read(3)
        assert content == b"\xef\xbb\xbf"  # UTF-8 BOM


def test_export_different_delimiters(sample_jsonl_file: Path, tmp_path: Path) -> None:
    """Test CSV export with different delimiters."""
    for delimiter in [",", "\t", ";"]:
        output_file = tmp_path / f"output_{delimiter.replace(chr(9), 'tab')}.csv"
        export_to_csv(
            sample_jsonl_file,
            output_file,
            mode=ColumnMode.DETAILED,
            delimiter=delimiter,
            progress=False,
        )

        assert output_file.exists()

        with output_file.open("r", encoding="utf-8") as f:
            content = f.read()
            # Verify delimiter is used (rough check)
            lines = content.split("\n")
            assert len(lines) > 1


def test_export_splits(sample_dataset_dir: Path, tmp_path: Path) -> None:
    """Test exporting train/val/test splits."""
    output_dir = tmp_path / "csv_output"
    export_splits_to_csv(
        sample_dataset_dir,
        output_dir,
        mode=ColumnMode.DETAILED,
    )

    assert output_dir.exists()

    for split in ["train", "val", "test"]:
        csv_file = output_dir / f"{split}.csv"
        assert csv_file.exists()

        with csv_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3


def test_export_empty_file(tmp_path: Path) -> None:
    """Test export handles empty JSONL file gracefully."""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("")

    output_file = tmp_path / "output.csv"
    export_to_csv(empty_file, output_file, mode=ColumnMode.DETAILED, progress=False)

    # Should create file but with no data rows (only header)
    if output_file.exists():
        with output_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) <= 1  # Just header or empty


def test_export_missing_fields(tmp_path: Path) -> None:
    """Test export handles missing fields gracefully."""
    jsonl_file = tmp_path / "test.jsonl"
    records = [
        {"url": "https://example.com/1", "content": "Some content"},
        {"title": "Title only"},
        {},
    ]
    with jsonl_file.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    output_file = tmp_path / "output.csv"
    export_to_csv(
        jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3  # All rows should be exported


def test_export_large_file(tmp_path: Path) -> None:
    """Test export handles large files efficiently."""
    jsonl_file = tmp_path / "large.jsonl"
    # Create a file with 1000 records
    with jsonl_file.open("w", encoding="utf-8") as f:
        for i in range(1000):
            record = {
                "url": f"https://example.com/{i}",
                "title": f"Article {i}",
                "content": f"Content for article {i}" * 10,
                "score": 0.8,
            }
            f.write(json.dumps(record) + "\n")

    output_file = tmp_path / "output.csv"
    export_to_csv(
        jsonl_file,
        output_file,
        mode=ColumnMode.DETAILED,
        progress=False,
    )

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1000

