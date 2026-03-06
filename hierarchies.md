# Hierarchies

Any folder structure planned or used in this project is documented here.
Before creating or changing any folder structure, it must be defined in this file first.

---

## Run outputs (tag-scoped)

Every training run is identified by a `{tag}`. Outputs are scoped to that tag.

```
plots/                          ← top-level folder for all checkpoint plots
    plots_{tag}/                ← checkpoint plots for run {tag}
        checkpoint_2min.png
        checkpoint_4min.png
        checkpoint_6min.png
        checkpoint_8min.png

results/                        ← top-level folder for all final visualizations
    results_{tag}/              ← final visualization suite for run {tag}
        01_training_curves.png
        02_easy_wins.png
        03_edge_cases.png
        04_failures.png
        05_confusion_matrix.png

logs/                           ← top-level folder for all training logs
    log_{tag}.log               ← training log for run {tag} (flat inside logs/)

pins/                           ← top-level folder for all pin drop data
    pins_{tag}/                 ← pin drops for run {tag}
        pins.txt                ← timestamped pin URLs collected during walk
```

**Rules:**
- Four fixed top-level folders: `plots/`, `results/`, `logs/`, `pins/`
- Inside `plots/` and `results/`: one subfolder per tag (`plots_{tag}/`, `results_{tag}/`)
- Inside `logs/`: files are flat — no subfolders, just `log_{tag}.log` directly
- Default tag = timestamp (e.g. `20260302_143000`)
- Tag is always passed at launch: `python nn_mnist_gpu.py --tag <tag>`
- Never write outputs outside these three top-level folders
