import hashlib
import json
import unicodedata
from pathlib import Path


def fingerprint(text):
    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def read_rows(path):
    rows = []
    ids = set()
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("id", "text", "source", "split"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"Line {line_no}: {field} must be a nonempty string")
        if type(row.get("label")) is not int or row["label"] not in (0, 1):
            raise ValueError(f"Line {line_no}: label must be integer 0 or 1")
        if row["split"] not in ("train", "validation", "test"):
            raise ValueError(f"Line {line_no}: invalid split")
        for field in ("group_id", "family"):
            if field in row and (not isinstance(row[field], str) or not row[field].strip()):
                raise ValueError(f"Line {line_no}: invalid {field}")
        if row["id"] in ids:
            raise ValueError(f"Duplicate id: {row['id']}")
        ids.add(row["id"])
        rows.append(row)
    if not rows:
        raise ValueError("Dataset is empty")
    return rows


def validate_partition(rows, name):
    if not rows or {r["label"] for r in rows} != {0, 1}:
        raise ValueError(f"{name} must contain both labels")
    hashes = [fingerprint(r["text"]) for r in rows]
    if len(hashes) != len(set(hashes)):
        raise ValueError(f"{name} contains normalized duplicates; curate these first")


def assert_disjoint(left, right, name):
    hashes = {fingerprint(r["text"]) for r in left}
    groups = {r["group_id"] for r in left if r.get("group_id")}
    if hashes & {fingerprint(r["text"]) for r in right}:
        raise ValueError(f"Text leakage across {name}")
    if groups & {r["group_id"] for r in right if r.get("group_id")}:
        raise ValueError(f"Group leakage across {name}")
