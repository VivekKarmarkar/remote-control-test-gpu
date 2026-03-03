# Hierarchies

Any folder structure planned or used in this project is documented here.
Before creating or changing any folder structure, it must be defined in this file first.

---

## Run outputs (tag-scoped)

Every training run is identified by a `{tag}`. Outputs are scoped to that tag.

```
plots_{tag}/                ← checkpoint plots for run {tag}
    checkpoint_2min.png
    checkpoint_4min.png
    checkpoint_6min.png
    checkpoint_8min.png

results_{tag}/              ← final visualization suite for run {tag}
    01_training_curves.png
    02_easy_wins.png
    03_edge_cases.png
    04_failures.png
    05_confusion_matrix.png

log_{tag}.log               ← training log for run {tag} (flat, no subfolder)
```

**Rules:**
- Multiple output files → folder (`plots_{tag}/`, `results_{tag}/`)
- Single output file → flat (`log_{tag}.log`)
- Default tag = timestamp (e.g. `20260302_143000`)
- Tag is always passed at launch: `python train.py --tag <tag>`
- Never hardcode `training.log`, `plots/`, or `results/` without a tag
