# Diacritic-Robustness Benchmark — Yoruba Sarcasm Detection

This document describes the benchmark protocol for evaluating the impact of
Yoruba diacritics on sarcasm detection models.

## Dataset overview

Source file: `Datasets/yoruba_sarcasm_data_compact.csv` (436 rows)  
Columns: `S/N`, `statement`, `target`, `source`, `text_origin`  
Labels: `sarcastic` (177 rows), `non-sarcastic` (259 rows)

---

## A. Diacritic view dataset

File: `Datasets/yoruba_sarcasm_data_diacritic_views.csv`  
Script: `scripts/make_diacritic_views.py`

Each row corresponds 1-to-1 with the compact dataset.

| Column | Description |
|---|---|
| `id` | Stable integer id (from `S/N`) |
| `statement_full` | **FULL** — exact original text, preserved verbatim |
| `statement_strip` | **STRIP** — all diacritics removed |
| `statement_noise_p25` | **NOISE-25** — diacritics removed with probability 0.25 |
| `statement_noise_p50` | **NOISE-50** — diacritics removed with probability 0.50 |
| `statement_noise_p75` | **NOISE-75** — diacritics removed with probability 0.75 |
| `target` | Label (`sarcastic` / `non-sarcastic`) |
| `source` | Data source (e.g. `BBC News`, `X`, `Instagram`) |
| `text_origin` | Origin type (e.g. `original`) |

### Unicode normalisation steps (STRIP and NOISE views)

1. Decompose the text to **NFD** (canonical decomposition).
2. Remove characters whose Unicode general category is **`Mn`**
   (non-spacing combining marks, i.e. diacritics).
   - For **STRIP**: remove every combining mark unconditionally.
   - For **NOISE**: remove each combining mark independently with
     probability *p* (0.25, 0.50, or 0.75).
3. Recompose the result to **NFC**.

### Noise method definition

Noise is applied **per combining-mark occurrence** (not per base character).
Each combining mark in the NFD-decomposed string is removed with
probability *p* using a single `random.Random(42)` instance that
processes all rows sequentially in source-file order
(row 1 first, noise_p25 → noise_p50 → noise_p75, then row 2, etc.).

This approach ensures:
- Results are identical across Python versions and platforms.
- The three noise levels for a given row use consecutive RNG draws,
  preserving inter-level correlation.

**Seed**: `42`

---

## B. Split files

Script: `scripts/make_splits.py`  
Manifest: `Splits/manifest.json`

### 1. Random stratified split (70 / 10 / 20)

Directory: `Splits/random_stratified_seed42/`

| File | Rows | Purpose |
|---|---|---|
| `train.csv` | 305 | Training set |
| `dev.csv` | 44 | Validation set |
| `test.csv` | 87 | Held-out test set |

- Stratified by `target` label.
- Seed: **42**

### 2. BBC held-out domain split

Directory: `Splits/bbc_heldout/`

| File | Rows | Purpose |
|---|---|---|
| `train.csv` | 136 | Non-BBC training data |
| `dev.csv` | 15 | 10 % of non-BBC pool, stratified, seed 42 |
| `test.csv` | 285 | All BBC News rows (held-out domain test) |

- `test.csv` contains all rows where `source == "BBC News"`.
- `dev.csv` is a 10 % stratified sample of the remaining (non-BBC) rows.
- `train.csv` is the remaining 90 % of non-BBC rows.
- Seed: **42**

---

## C. Regenerating artifacts

From the repo root:

```bash
python scripts/make_diacritic_views.py
python scripts/make_splits.py
```

Both scripts require only the Python standard library (no external packages).
They read `Datasets/yoruba_sarcasm_data_compact.csv` and write outputs to
the paths listed above.

Both scripts include an assertion-based reproducibility check that will
raise an error if results differ from a fresh run.
