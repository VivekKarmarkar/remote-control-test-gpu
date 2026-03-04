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

2. **Live training monitor** — every git push from train.py is logged to the
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

## Scientific report with data analysis

A LaTeX report covering the full project — what was done, how it worked, and
the data to back it up. Includes:

- Training run data analysis (accuracy curves, variance across runs, etc.)
- Code snippets showing key architectural decisions
- Cylinder chart for CPU/GPU divide — the circle shows the percentage split
  between CPU and GPU work, the height shows the time spent on each. Two
  dimensions: what proportion of work goes where, and how long each takes.
- Discussion of iterative design, the feedback loop, and the core insight
- Experimental results from trialrun groups 6, 7, and 8

### Why this matters

The web app doesn't launch training — Claude Code does. That's the magic
moment. The web app is the proof that it all works: a neural network was
trained on a laptop GPU from a phone via Claude Code's remote control while
out on a walk.
