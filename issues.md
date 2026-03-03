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

## Issue 3: Claude-related failure modes

Three recurring failure modes observed from the AI assistant (Claude) during development:

**1. Breaking working things while adding new features**

When adding the `--tag` feature and retry logic to `git_push()`, the synchronous
`subprocess.run` call with no timeout was left in place. When the network dropped,
the git push hung indefinitely — freezing the entire training loop for over an hour.
New features were added on top of a latent design flaw that hadn't been fixed first.
This is exactly what Philosophy 4 warns against.

**2. Sycophancy**

Tendency to agree, validate, and proceed rather than push back when something is
unclear or wrong. Asking performative clarifying questions instead of genuine ones.
Pretending to understand when not understanding. This is worse than just being wrong —
it wastes time and creates false confidence. If something is unclear, say so directly.
If a spec is ambiguous, flag it before writing code, not after.

**3. Hallucination / misremembering specs**

Getting folder paths wrong after being told the correct hierarchy (e.g. writing
`plots_{tag}/` at root instead of `plots/plots_{tag}/`). Implementing details that
were never specified. Not reading the relevant doc files before writing code.
The fix: read `hierarchies.md`, `philosophies.md`, `plotting_rules.md`, and
`sacred_rules.md` before every plan and before every implementation.
