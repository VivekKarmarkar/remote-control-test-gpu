# Plotting Rules

Every rule here was chosen deliberately. Every rule has a reason.
Before writing a single line of plotting code, read this entire file.
Before changing any rule, it must be updated here first.

---

## Why we make plots at all

We are training on a GPU remotely, from a phone, while walking outdoors.
The terminal is invisible. The training log is invisible. The only window into
what is happening is GitHub. When a plot appears on GitHub, we know training
is alive and progressing. When the final suite appears, we know training
succeeded. If a plot is ugly, misleading, or unreadable on a phone, it has
failed its purpose. If it does not appear on schedule, something is broken.

The plots ARE the feedback system. They are not decoration.

---

## Style rules (applied to every single plot without exception)

### Color palette — Okabe-Ito

We use the Okabe-Ito colorblind-safe palette. This is the standard palette
recommended by Nature and Science for scientific figures. Approximately 8% of
men have some form of color blindness. A figure that is unreadable to 8% of
your audience is a bad figure. We do not use default matplotlib blue/orange,
we do not use red/green, we do not use arbitrary colors. We use these and only
these:

| Role                | Color name  | Hex code  |
|---------------------|-------------|-----------|
| Training data       | Blue        | `#0072B2` |
| Validation data     | Orange      | `#E69F00` |
| Errors / wrong pred | Vermillion  | `#D55E00` |
| Neutral / other     | Gray        | `#999999` |
| Correct (highlight) | Blue        | `#0072B2` |

No other colors are used on the data. Borders and highlights around sample
cells use green (easy wins), amber (edge cases), red (failures) — these are
UI indicators, not data colors.

### Font — DejaVu Sans

We use DejaVu Sans (sans-serif). This is the default matplotlib font and the
one that renders most cleanly on screens and at low DPI. We do not use serif
fonts. We do not use custom fonts that require installation.

Font sizes:
- Axis labels: 9pt
- Tick labels: 7pt
- Titles: 10pt bold
- Legend: 8pt
- Annotations: 8pt

### Spines — left and bottom only

We remove the top spine and the right spine. We keep only the left (y-axis)
and bottom (x-axis) spines. This is the Nature/Science convention. It removes
visual clutter and focuses the reader on the data. Charts with four-sided
boxes look like spreadsheets. We are not making spreadsheets.

```python
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
```

### Grid — horizontal only, light, behind data

Grid lines help the eye read values. But they must not compete with the data.
Rules:
- Horizontal grid lines only (no vertical)
- Color: `#cccccc` (light gray)
- Line width: 0.5pt
- `ax.set_axisbelow(True)` — grid goes behind all plotted data
- No grid on image panels (MNIST digit panels have no grid)

### DPI — 150

The output is viewed on a phone. DPI 150 is high enough to be readable on a
phone screen, low enough that the file size stays reasonable for GitHub.
We do not use DPI 72 (too blurry on phone). We do not use DPI 300 (too heavy
for a quick GitHub push during training).

```python
fig.savefig(path, dpi=150, bbox_inches='tight', pad_inches=0.05)
```

### Legend — no frame, 8pt font

Legends with frames add visual clutter. The frame adds no information.
We always use `frameon=False` in legend calls.

```python
ax.legend(frameon=False, fontsize=8)
```

---

## Checkpoint plots (4 total — pushed at 2, 4, 6, 8 minutes)

### Purpose

These are live feedback during training. When you see a checkpoint plot on
GitHub, you know: training is alive, the GPU is working, and progress is
being made. The purpose is verification, not analysis. Verification must be
possible at a glance on a phone screen.

### Layout — 2 panels, side by side

```
[ Loss vs Time ]  |  [ Accuracy vs Time ]
```

**Left panel: Cross-Entropy Loss vs elapsed time (seconds)**
- X-axis: elapsed time in seconds
- Y-axis: cross-entropy loss value
- Training loss: solid Blue (#0072B2)
- Validation loss: dashed Orange (#E69F00)
- No markers (lines only — cleaner at small size)
- Axis label: "Time (s)" / "Loss"
- Title: "Loss"

**Right panel: Accuracy (%) vs elapsed time (seconds)**
- X-axis: elapsed time in seconds
- Y-axis: accuracy in percent (0–100)
- Training accuracy: solid Blue (#0072B2)
- Validation accuracy: dashed Orange (#E69F00)
- Annotate the current best validation accuracy:
  text annotation pointing to the peak: "Best val: XX.X%"
- Axis label: "Time (s)" / "Accuracy (%)"
- Title: "Accuracy"

**Figure title:** "Checkpoint — X min  |  Epoch N  |  Val acc: XX.X%"

**File path:** `plots/plots_{tag}/checkpoint_{N}min.png`

---

## Final visualization suite (5 plots — pushed after training ends)

### Purpose

These are the full post-mortem analysis of the run. They answer the complete
picture of what the model learned, where it excels, where it struggles, and
where it fails. The suite is pushed once, at the end, after all training is
done. These are not live feedback — they are the final record of the experiment.

---

### 01_training_curves.png — Did training actually work?

**Purpose:** The definitive training record. Shows the complete loss and
accuracy curves for the entire run. This is the first thing you check to
confirm training succeeded — did loss go down? Did accuracy go up? Did
validation track training or diverge?

**Layout:** 2 panels, side by side (same as checkpoint but full run)

- Same panel design as checkpoint plots
- Additionally: mark the best validation epoch with a vertical dashed gray
  line across both panels
- Annotate the best val accuracy: "Best val acc: XX.X% @ Xs"

**File path:** `results/results_{tag}/01_training_curves.png`

---

### 02_easy_wins.png — Where the model excels

**Purpose:** Shows the 12 validation samples where the model is most
confidently correct. These are the "easy" cases — the model had no doubt.
This confirms the model has genuinely learned the core patterns of each class.

**Layout:** 4 rows × 3 columns = 12 cells. Each cell is split into 2 panes:

```
[ MNIST image ] | [ softmax bar chart ]
```

**Left pane (image):**
- MNIST digit rendered as grayscale image
- No interpolation (`interpolation='nearest'`)
- No axis ticks

**Right pane (softmax bars):**
- Horizontal bar chart of all 10 softmax probabilities
- Correct class bar: Blue (#0072B2)
- All other bars: Gray (#999999)
- X-axis: 0 to 1 (probability)
- Y-axis: digit labels 0–9

**Sample selection:** Highest confidence correct predictions (sorted by
confidence of the correct class, descending)

**Cell title:** `True: X  Pred: X  (99.X%)`

**Cell border:** Green — signals correct, high confidence

**Figure subtitle:** "Easy wins — high-confidence correct predictions"

**File path:** `results/results_{tag}/02_easy_wins.png`

---

### 03_edge_cases.png — Where it gets hard

**Purpose:** Shows the 12 validation samples where the model was correct but
uncertain. These are the hardest cases the model still got right. The softmax
bars show competition between the top-2 or top-3 classes — the model was not
sure but picked correctly. This reveals which digit pairs are visually similar
and where the decision boundary is thin.

**Layout:** Identical structure to 02_easy_wins.png

**Sample selection:** Correct predictions with the lowest confidence (sorted
by confidence of the correct class, ascending — most uncertain correct preds)

**Right pane:** softmax bars show spread across top 2–3 classes, revealing
ambiguity

**Cell title:** `True: X  Pred: X  (conf: XX%)`

**Cell border:** Amber/yellow — signals caution, uncertain

**Figure subtitle:** "Edge cases — correct but uncertain"

**File path:** `results/results_{tag}/03_edge_cases.png`

---

### 04_failures.png — Where it breaks

**Purpose:** Shows the 12 most confidently wrong predictions. These are the
worst failures — the model was certain, and it was wrong. The softmax bars
show the wrong predicted class in Vermillion and the true class in Blue, so
you can immediately see what the model thought it was looking at vs what it
actually was. This is where the most interesting information lives — confident
failures reveal systematic weaknesses in the model.

**Layout:** Identical structure to 02_easy_wins.png

**Sample selection:** Wrong predictions, sorted by confidence of the wrong
answer (most confidently wrong first)

**Right pane (softmax bars):**
- Predicted (wrong) class bar: Vermillion (#D55E00) — the mistake
- True (correct) class bar: Blue (#0072B2) — what it should have been
- All other bars: Gray (#999999)

**Cell title:** `True: X  Pred: Y  (conf: XX%)`

**Cell border:** Red — signals failure

**Figure subtitle:** "Failures — what the model got wrong and why"

**File path:** `results/results_{tag}/04_failures.png`

---

### 05_confusion_matrix.png — Full error map

**Purpose:** The complete picture of every error pattern across all 10,000
validation samples. Shows which digit pairs get confused most often. The
classic pairs are 4↔9, 3↔8, 5↔6 — digits that look similar. A strong model
has a dark diagonal and near-zero off-diagonal. This is the single most
information-dense plot in the suite.

**Layout:** Single large heatmap, 10×10

- Rows: true digit (0–9)
- Columns: predicted digit (0–9)
- Values: **row-normalized** — each cell is the fraction of true-class samples
  predicted as each digit (so each row sums to 1.0 or 100%)
  Why row-normalize? Because class sizes may be unequal. Raw counts would
  make common classes look worse. Row normalization gives the per-class error
  rate, which is the meaningful metric.
- Colormap: sequential Blue (light = near zero, dark = near 1.0)
  Must be perceptually uniform — use `Blues` from matplotlib
  Do NOT use diverging colormaps (no red-white-blue)
- Annotate each cell with the count (raw count, not the normalized value)
  so both the pattern (color) and the scale (count) are visible
- Diagonal: correct predictions — should be dark
- Off-diagonal: errors — should be near-zero/light

**Axis labels:**
- Y-axis: "True Label"
- X-axis: "Predicted Label"
- Title: "Confusion Matrix — Validation Set (N=10,000)"

**File path:** `results/results_{tag}/05_confusion_matrix.png`

---

## What gets pushed to GitHub and when

| What                          | When               | Path                              |
|-------------------------------|--------------------|-----------------------------------|
| `checkpoint_2min.png`         | At 2 min mark      | `plots/plots_{tag}/`              |
| `checkpoint_4min.png`         | At 4 min mark      | `plots/plots_{tag}/`              |
| `checkpoint_6min.png`         | At 6 min mark      | `plots/plots_{tag}/`              |
| `checkpoint_8min.png`         | At 8 min mark      | `plots/plots_{tag}/`              |
| `01_training_curves.png`      | After training ends| `results/results_{tag}/`          |
| `02_easy_wins.png`            | After training ends| `results/results_{tag}/`          |
| `03_edge_cases.png`           | After training ends| `results/results_{tag}/`          |
| `04_failures.png`             | After training ends| `results/results_{tag}/`          |
| `05_confusion_matrix.png`     | After training ends| `results/results_{tag}/`          |

**The log file is NOT pushed to GitHub.** It stays local. GitHub is a visual
feedback channel for plots — not a log aggregator. Pushing a text log file
adds noise to the repo and buys nothing visible on a phone.

**git add scope at each checkpoint:**
```bash
git add plots/plots_{tag}/
```

**git add scope at end:**
```bash
git add results/results_{tag}/
```
