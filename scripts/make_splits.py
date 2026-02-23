"""
make_splits.py
==============
Generate deterministic train/dev/test splits for the compact Yoruba
sarcasm dataset.

Two split strategies are produced:

1. Random stratified split (70 / 10 / 20) — seed 42
   Stratified by ``target`` label.
   Output directory: ``Splits/random_stratified_seed42/``

2. BBC-held-out domain split
   - test  : all rows where source == "BBC News"
   - train : all remaining rows
   - dev   : 10 % of the train pool, stratified by ``target``, seed 42
   Output directory: ``Splits/bbc_heldout/``

A manifest JSON is written to ``Splits/manifest.json`` documenting seeds,
proportions, and source file.

Requires: Python ≥ 3.8, pandas (for stratified splitting convenience).

Usage
-----
  python scripts/make_splits.py
"""

import csv
import json
import os
import random

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_CSV = os.path.join(_REPO_ROOT, "Datasets", "yoruba_sarcasm_data_compact.csv")
SPLITS_DIR = os.path.join(_REPO_ROOT, "Splits")

RANDOM_DIR = os.path.join(SPLITS_DIR, "random_stratified_seed42")
BBC_DIR = os.path.join(SPLITS_DIR, "bbc_heldout")

SEED = 42
BBC_SOURCE = "BBC News"
DEV_FRAC_BBC = 0.10  # 10 % of the non-BBC pool used as dev

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_csv(path: str):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: str, rows: list, fieldnames: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def _stratified_split(rows: list, fracs: list, label_key: str, seed: int):
    """
    Split *rows* into len(fracs) parts with proportions matching *fracs*.
    Stratification is done by *label_key*.
    Returns a list of row-lists with the same length as *fracs*.

    Algorithm
    ---------
    1. Group rows by label.
    2. For each label group shuffle with *seed* then split by fracs.
    3. Concatenate across groups per split index.
    """
    from collections import defaultdict

    groups = defaultdict(list)
    for row in rows:
        groups[row[label_key]].append(row)

    splits = [[] for _ in fracs]
    for label, grp in sorted(groups.items()):
        rng = random.Random(seed)
        rng.shuffle(grp)
        n = len(grp)
        starts = [0]
        for f in fracs[:-1]:
            starts.append(starts[-1] + round(n * f))
        starts.append(n)
        for i in range(len(fracs)):
            splits[i].extend(grp[starts[i] : starts[i + 1]])

    # Shuffle each final split so labels are interleaved
    for i, split in enumerate(splits):
        rng = random.Random(seed + i)
        rng.shuffle(split)

    return splits


# ---------------------------------------------------------------------------
# Split 1: Random stratified 70/10/20
# ---------------------------------------------------------------------------


def make_random_stratified(rows: list, fieldnames: list) -> dict:
    train, dev, test = _stratified_split(rows, [0.70, 0.10, 0.20], "target", SEED)

    _write_csv(os.path.join(RANDOM_DIR, "train.csv"), train, fieldnames)
    _write_csv(os.path.join(RANDOM_DIR, "dev.csv"), dev, fieldnames)
    _write_csv(os.path.join(RANDOM_DIR, "test.csv"), test, fieldnames)

    total = len(train) + len(dev) + len(test)
    assert total == len(rows), (
        f"Split row count mismatch: {total} != {len(rows)}. "
        "Some rows may have been lost or duplicated during splitting."
    )

    print(
        f"random_stratified_seed42: train={len(train)}, "
        f"dev={len(dev)}, test={len(test)}"
    )
    return {
        "strategy": "random_stratified",
        "seed": SEED,
        "proportions": {"train": 0.70, "dev": 0.10, "test": 0.20},
        "stratify_by": "target",
        "counts": {"train": len(train), "dev": len(dev), "test": len(test)},
        "directory": "Splits/random_stratified_seed42",
    }


# ---------------------------------------------------------------------------
# Split 2: BBC held-out
# ---------------------------------------------------------------------------


def make_bbc_heldout(rows: list, fieldnames: list) -> dict:
    bbc_rows = [r for r in rows if r["source"] == BBC_SOURCE]
    non_bbc = [r for r in rows if r["source"] != BBC_SOURCE]

    assert bbc_rows, "No BBC News rows found!"

    # Dev: stratified 10 % sample from non-BBC pool
    dev_size_frac = DEV_FRAC_BBC
    remaining_frac = 1.0 - dev_size_frac
    train_pool, dev = _stratified_split(
        non_bbc, [remaining_frac, dev_size_frac], "target", SEED
    )

    _write_csv(os.path.join(BBC_DIR, "train.csv"), train_pool, fieldnames)
    _write_csv(os.path.join(BBC_DIR, "dev.csv"), dev, fieldnames)
    _write_csv(os.path.join(BBC_DIR, "test.csv"), bbc_rows, fieldnames)

    total = len(train_pool) + len(dev) + len(bbc_rows)
    assert total == len(rows), (
        f"Split row count mismatch: {total} != {len(rows)}. "
        "Some rows may have been lost or duplicated during splitting."
    )

    print(
        f"bbc_heldout: train={len(train_pool)}, "
        f"dev={len(dev)}, test={len(bbc_rows)}"
    )
    return {
        "strategy": "bbc_heldout",
        "seed": SEED,
        "test_filter": f'source == "{BBC_SOURCE}"',
        "dev_proportion_of_train_pool": DEV_FRAC_BBC,
        "stratify_by": "target",
        "counts": {
            "train": len(train_pool),
            "dev": len(dev),
            "test": len(bbc_rows),
        },
        "directory": "Splits/bbc_heldout",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    rows = _read_csv(SRC_CSV)
    assert rows, "Source CSV is empty!"

    fieldnames = list(rows[0].keys())

    os.makedirs(RANDOM_DIR, exist_ok=True)
    os.makedirs(BBC_DIR, exist_ok=True)

    manifest = {
        "source_file": "Datasets/yoruba_sarcasm_data_compact.csv",
        "total_rows": len(rows),
        "splits": [
            make_random_stratified(rows, fieldnames),
            make_bbc_heldout(rows, fieldnames),
        ],
    }

    manifest_path = os.path.join(SPLITS_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Written manifest → {manifest_path}")


if __name__ == "__main__":
    main()
