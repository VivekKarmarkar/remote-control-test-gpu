# Insights

## Core insight

The first run failed. From that failure came the realization: I need feedback
every 2 minutes from my phone. Everything else emerged from that.

## What emerged from the core insight

1. **Git autopush hook** — checkpoint plots pushed to GitHub every 2 minutes,
   giving real-time visibility from the phone without any intervention

2. **nohup as free insurance** — technically redundant (the laptop is all that
   matters once training launches), but costs nothing and protects against
   edge cases

3. **NN hyperparameters** — Adam lr=0.001, 3x4096 MLP, 480s duration, 120s
   checkpoints — tuned to produce visible progress within the feedback window

4. **CPU/GPU divide** — everything that matters (data, model, training) lives
   on the GPU. CPU only handles logging and git pushes. No DataLoader, no
   disk I/O, no CPU-GPU transfers during training

5. **Infrastructural requirements** — phone charged and topped up, Anthropic
   servers stable, remote control working, auto-suspend disabled. The magic
   flow only works when all infrastructure is solid

## The process

None of this was specced upfront. The specs were non-optimal given the model's
capacity — not underspecified, just calibrated to what seemed right for a
capable model working on a well-known problem. The model got most things right
and one thing wrong. The feedback loop made it possible to catch that and
iterate. Iterative design, not issue resolution.
