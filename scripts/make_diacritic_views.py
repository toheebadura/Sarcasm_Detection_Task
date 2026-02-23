"""
make_diacritic_views.py
=======================
Generate ``Datasets/yoruba_sarcasm_data_diacritic_views.csv`` from the
compact Yoruba sarcasm dataset.

Three text views are produced in addition to the original:
  FULL   – exact original statement
  STRIP  – all diacritics (Unicode combining marks, category Mn) removed
  NOISE  – combining marks removed with probability p (0.25 / 0.50 / 0.75)

Unicode normalisation steps (STRIP and NOISE):
  1. Decompose to NFD.
  2. Remove characters whose Unicode category is "Mn" (combining marks).
     For NOISE views each combining mark is removed with probability p.
  3. Recompose to NFC.

Noise is applied per combining-mark occurrence (not per base character),
using a global random.Random(42) instance so results are reproducible
across runs regardless of platform.

Usage
-----
  python scripts/make_diacritic_views.py

Output
------
  Datasets/yoruba_sarcasm_data_diacritic_views.csv  (UTF-8, quoted)
"""

import csv
import os
import random
import unicodedata

# ---------------------------------------------------------------------------
# Paths (relative to repo root; script must be run from repo root OR resolved
# via __file__)
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_CSV = os.path.join(_REPO_ROOT, "Datasets", "yoruba_sarcasm_data_compact.csv")
DST_CSV = os.path.join(
    _REPO_ROOT, "Datasets", "yoruba_sarcasm_data_diacritic_views.csv"
)

NOISE_SEED = 42


# ---------------------------------------------------------------------------
# Core text transformations
# ---------------------------------------------------------------------------


def strip_diacritics(text: str) -> str:
    """Remove ALL Unicode combining marks (Mn) via NFD decomposition."""
    nfd = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


def noise_diacritics(text: str, p: float, rng: random.Random) -> str:
    """Remove each combining mark with probability *p* (deterministic via rng)."""
    nfd = unicodedata.normalize("NFD", text)
    result = []
    for ch in nfd:
        if unicodedata.category(ch) == "Mn":
            if rng.random() < p:
                continue  # remove this combining mark
        result.append(ch)
    return unicodedata.normalize("NFC", "".join(result))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    rng = random.Random(NOISE_SEED)

    with open(SRC_CSV, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert rows, "Source CSV is empty!"

    # Validate and normalise the id column
    seen_ids: set = set()
    out_rows = []
    for row in rows:
        raw_id = row["S/N"].strip()
        assert raw_id.isdigit(), (
            f"Expected numeric S/N value, got: {raw_id!r}. "
            "Please verify the source CSV format."
        )
        id_int = int(raw_id)
        assert id_int not in seen_ids, f"Duplicate S/N: {id_int}"
        seen_ids.add(id_int)

        stmt = row["statement"]
        out_rows.append(
            {
                "id": id_int,
                "statement_full": stmt,
                "statement_strip": strip_diacritics(stmt),
                "statement_noise_p25": noise_diacritics(stmt, 0.25, rng),
                "statement_noise_p50": noise_diacritics(stmt, 0.50, rng),
                "statement_noise_p75": noise_diacritics(stmt, 0.75, rng),
                "target": row["target"],
                "source": row["source"],
                "text_origin": row["text_origin"],
            }
        )

    assert len(out_rows) == len(rows), "Row count mismatch after processing!"

    fieldnames = [
        "id",
        "statement_full",
        "statement_strip",
        "statement_noise_p25",
        "statement_noise_p50",
        "statement_noise_p75",
        "target",
        "source",
        "text_origin",
    ]

    with open(DST_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Written {len(out_rows)} rows → {DST_CSV}")

    # Basic reproducibility check: re-read and compare row 0
    rng2 = random.Random(NOISE_SEED)
    first = rows[0]
    stmt0 = first["statement"]
    check_p25 = noise_diacritics(stmt0, 0.25, rng2)
    assert check_p25 == out_rows[0]["statement_noise_p25"], (
        "Reproducibility check failed for row 0 noise_p25"
    )
    print("Reproducibility check passed.")


if __name__ == "__main__":
    main()
