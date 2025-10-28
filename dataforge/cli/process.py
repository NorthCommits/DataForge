from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List

from bs4 import BeautifulSoup


def _iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _clean_text(text: str) -> str:
    try:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ")
    except Exception:
        pass
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_low_quality(text: str) -> bool:
    if len(text) < 100:
        return True
    non_alnum_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
    if non_alnum_ratio > 0.3:
        return True
    return False


def _exact_dedup(records: List[Dict]) -> List[Dict]:
    seen = set()
    out: List[Dict] = []
    for r in records:
        h = hash(r.get("content", ""))
        if h in seen:
            continue
        seen.add(h)
        out.append(r)
    return out


def _fuzzy_dedup(records: List[Dict], threshold: float = 0.9) -> List[Dict]:
    kept: List[Dict] = []
    for r in records:
        txt = r.get("content", "")
        if not txt:
            continue
        duplicate = False
        for k in kept:
            if SequenceMatcher(None, txt, k.get("content", "")).ratio() >= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(r)
    return kept


def process_raw_to_dataset(input_path: Path, output_dir: Path) -> Dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = list(_iter_jsonl(input_path))
    total = len(records)

    for r in records:
        content = r.get("content") or ""
        r["content"] = _clean_text(content)

    records = [r for r in records if r.get("content") and not _is_low_quality(r["content"])]
    after_filter = len(records)

    records = _exact_dedup(records)
    records = _fuzzy_dedup(records)
    after_dedup = len(records)

    n = len(records)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    train = records[:n_train]
    val = records[n_train:n_train + n_val]
    test = records[n_train + n_val:]

    def _save_split(name: str, rows: List[Dict]) -> None:
        p = output_dir / f"{name}.jsonl"
        with p.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    _save_split("train", train)
    _save_split("val", val)
    _save_split("test", test)

    card = {
        "name": output_dir.name,
        "source": str(input_path),
        "num_total": total,
        "num_after_filter": after_filter,
        "num_after_dedup": after_dedup,
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
    }
    (output_dir / "dataset_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

    removed = total - after_dedup
    return {"total": total, "removed": removed, "final": after_dedup}


