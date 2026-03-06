# Ideas

## The web app

A single web app (GitHub Pages) that serves as live proof that a neural
network was trained remotely on a laptop GPU from a phone while walking.

### What it does

1. **Finger-sketch inference** — draw a digit on a touch-screen canvas, the
   model predicts it in the browser. Works before and after training.
   - Pre-training: random weights, garbage predictions
   - Post-training: trained weights, accurate predictions
   - The before/after is the proof

2. **Live training monitor** — every git push from nn_mnist_gpu.py is logged to the
   web app. Checkpoint plots appear as training progresses. You watch training
   happen from your phone while walking.

3. **Location capture** — every interaction (sketch, view, page open) captures
   lat/lng via the browser Geolocation API. No post-hoc correlation — the
   proof is baked into the moment of interaction.

4. **Commit metadata** — every git push embeds laptop time and location. The
   distance between the laptop and the phone IS the proof of remote control.

### The flow on a walk

1. Open web app, draw a digit — garbage prediction (no training yet)
2. Switch to Claude Code, launch training (the magic moment)
3. Watch checkpoint plots appear on the web app every 2 minutes
4. Training completes, new weights available
5. Draw a digit again — model nails it

All while walking. All location-tracked.

### The map

All events on one map over a walking route:

- **Sketch (pre-training)** — where you drew a digit and got garbage
- **Launch** — where you kicked off training via Claude Code
- **Checkpoints** — where you were when each checkpoint appeared
- **Sketch (post-training)** — where you drew a digit and the model got it right

Each marker shows phone location (where you were) and laptop location (where
training happened). The gap between them is the proof.

### Implementation

- HTML5 `<canvas>` with touch events for drawing
- Resize to 28x28, normalize to match MNIST preprocessing
- Model weights exported as JSON (4 weight matrices, 4 bias vectors)
- Inference in plain JavaScript — matrix multiply and ReLU, no ML framework
- Browser Geolocation API for location capture
- GitHub Pages hosting — no server needed
- Polls or listens for new git pushes to update training progress

## Cylinder chart: CPU/GPU operation profiling

A cylinder chart where:
- **Pie (circular cross-section)**: percentage of total work done by CPU vs GPU
- **Height per slice**: time per operation for that category

This requires thoroughly tracing EVERY operation in nn_mnist_gpu.py and categorizing
each as CPU or GPU, with actual measured time per operation.

### GPU operations to profile

**Per-epoch training loop (runs ~100 times):**
- `torch.randperm(N, device='cuda')` — random permutation generation on GPU
- `X_train[perm]` — tensor indexing/shuffling on GPU
- `y_train[perm]` — tensor indexing/shuffling on GPU
- `optimizer.zero_grad()` — zero all parameter gradients on GPU
- `model(X_batch)` — forward pass through 3 linear layers + ReLU on GPU
  (784→4096→4096→4096→10, done per batch, ~117 batches per epoch)
- `criterion(out, y_batch)` — CrossEntropyLoss computation on GPU
- `loss.backward()` — backward pass, gradient computation on GPU
- `optimizer.step()` — Adam parameter update on GPU
- `out.argmax(1)` — argmax on GPU (per batch)
- `(out.argmax(1) == y_batch).sum()` — comparison and reduction on GPU

**Per-epoch validation (runs ~100 times):**
- `model(X_val)` — single forward pass on full 10K validation set on GPU
- `criterion(val_out, y_val)` — loss on GPU
- `val_out.argmax(1)` — argmax on GPU
- `(val_out.argmax(1) == y_val).sum()` — comparison and reduction on GPU

**One-time setup:**
- `.cuda()` calls — CPU→GPU data transfer for X_train, y_train, X_val, y_val
- `MLP().cuda()` — model parameter allocation on GPU

**Final plots (runs once):**
- `model(X_val)` in `_get_predictions()` — forward pass on GPU
- `torch.softmax(logits, dim=1)` — softmax on GPU
- `.cpu().numpy()` — GPU→CPU transfer of predictions (sync point)

### CPU operations to profile

**Per-epoch (runs ~100 times):**
- `time.time()` — system clock read
- `loss.item()` — GPU→CPU sync + scalar transfer
- `.sum().item()` — GPU→CPU sync + scalar transfer
- `criterion(...).item()` — GPU→CPU sync + scalar transfer (validation)
- `print()` via TeeLogger — write to stdout (/dev/null) + log file + flush
- `metrics['time'].append(...)` etc. — Python list appends (6 per epoch)

**Per-checkpoint (runs 4 times):**
- `plot_checkpoint()` — full matplotlib figure: create fig, plot 4 lines,
  annotate, suptitle, tight_layout, savefig (PNG encode + disk write), close
- `git_push()` thread creation — `threading.Thread()` + `.start()`
- Inside git thread: `subprocess.run(["git", "add", ...])` — git index update
- Inside git thread: `subprocess.run(["git", "commit", ...])` — git commit
- Inside git thread: `subprocess.run(["git", "push", ...])` — network I/O
  to GitHub (up to 3 retries with 5s delay, 30s timeout)

**Final visualizations (runs once):**
- `plot_training_curves()` — matplotlib figure with 4 lines + annotations
- `plot_easy_wins()` — 12-sample grid, each with image + bar chart (24 axes)
- `plot_edge_cases()` — 12-sample grid (24 axes)
- `plot_failures()` — 12-sample grid (24 axes)
- `plot_confusion_matrix()` — 10x10 heatmap with text annotations
- `np.where()`, `np.argsort()` — numpy sample selection
- `X_val[i].cpu().numpy().reshape(28, 28)` — per-sample GPU→CPU transfer
- Final `git_push()` + `t.join(timeout=60)` for all pending threads

**One-time setup:**
- `argparse` — argument parsing
- `os.makedirs()` — directory creation (3 calls)
- `datasets.MNIST(download=True)` — disk read (or download)
- `.float().div(255).view(-1, 784)` — tensor preprocessing on CPU before
  transfer to GPU
- `TeeLogger` setup — file open
- `setup_style()` — matplotlib rcParams
- `sum(p.numel() for p in model.parameters())` — parameter count

### Profiling approach

Run a dedicated profiling session that wraps each operation with
`time.perf_counter()` before and after. Aggregate across all epochs.
Output raw timing data as JSON for the cylinder chart.

### Expected result

GPU slice: massive area (vast majority of compute), tiny height (each
operation is microseconds/milliseconds — GPU is fast per operation).

CPU slice: tiny area (minimal compute), taller height (git push is seconds,
matplotlib is milliseconds-to-seconds per plot, `.item()` sync points are
microseconds but they block).

## Scientific report with data analysis

A LaTeX report covering the full project — what was done, how it worked, and
the data to back it up. Includes:

- Training run data analysis (accuracy curves, variance across runs, etc.)
- Code snippets showing key architectural decisions
- Cylinder chart from the profiling above
- Discussion of iterative design, the feedback loop, and the core insight
- Experimental results from trialrun groups 6, 7, and 8

### Why this matters

The web app doesn't launch training — Claude Code does. That's the magic
moment. The web app is the proof that it all works: a neural network was
trained on a laptop GPU from a phone via Claude Code's remote control while
out on a walk.
