# Sarcasm Detection Task

This project is an individual preliminary work on Natural Language Processing, focusing on detecting sarcasm in the dataset. It explores machine learning models as the baseline models. Moreover, it implements deep learning methods that would aid in discovering more complex patterns from the dataset.

## Diacritic-Robustness Benchmark & Official Splits

Publication-ready benchmark artifacts for the Yoruba sarcasm dataset are available:

- **Diacritic views**: `Datasets/yoruba_sarcasm_data_diacritic_views.csv`
  — FULL / STRIP / NOISE-25 / NOISE-50 / NOISE-75 text views per row.
- **Random stratified splits** (70/10/20, seed 42): `Splits/random_stratified_seed42/`
- **BBC held-out domain splits**: `Splits/bbc_heldout/`
- **Split manifest**: `Splits/manifest.json`

See [`Datasets/README_diacritic_benchmark.md`](Datasets/README_diacritic_benchmark.md)
for full protocol documentation.

To regenerate all artifacts from scratch:

```bash
python scripts/make_diacritic_views.py
python scripts/make_splits.py
```
