# Issues

## Issue 1: Data loader was the weakest link

The training pipeline used a standard PyTorch DataLoader with `num_workers=4` to load
MNIST from disk. Even though the GPU was available, it sat idle between batches waiting
for the CPU to load and transfer data. GPU utilization was effectively 0%.

**The fix:** Generate synthetic data directly as GPU tensors at startup. No DataLoader,
no disk I/O, no CPU-GPU transfers during training. Everything lives in GPU memory from
the start so the GPU is the bottleneck — not the scaffolding around it.

> "A chain is only as strong as its weakest link."

## Issue 2: Remote control session breaks after ~20 minutes

The remote control session disconnects after roughly 20-30 minutes, cutting off access
from the phone. Root cause unknown — needs diagnosis.

See `hacks.md` (Hack 1) and `tests.md` (Tests 1 & 2).
