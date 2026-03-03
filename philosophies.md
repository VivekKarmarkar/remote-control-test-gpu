# Philosophies

## Philosophy 1: A chain is only as strong as its weakest link

If the goal is to harness GPU speed, then every other part of the pipeline must be
designed so it is not the bottleneck. The GPU speedup is only as good as the slowest
non-GPU component allows it to be. Before optimizing GPU utilization, eliminate all
other sources of friction — data loading, CPU transfers, disk I/O, scaffolding — so
the GPU is the only thing that matters.

## Philosophy 2: Lock in specs before executing

Remote control leaves no room for loose specs. If something needs to be discussed,
clarified, or locked in — do it in plan mode with as many clarifying questions as
needed, before writing a single line of code or firing off a run. Ambiguity discovered
mid-execution is far more costly than time spent aligning upfront.

## Philosophy 3: Quick verifiable outputs drive design, not the other way around

The need for fast, meaningful feedback pushes to GitHub is the philosophy that defines
every design parameter — how large the network is, how many epochs between checkpoints,
what optimizer is used, how many samples are trained on. The checkpoint interval is not
an arbitrary number chosen after the fact; it is derived from how quickly the user needs
to verify progress from their phone. If a checkpoint takes too long to arrive, the
design is wrong — not the interval.

## Philosophy 4: Don't FUCKING break things that work while adding new features

**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**
**Don't FUCKING break things that work while adding new features.**

## Philosophy 5: GitHub is the only feedback channel that survives

Remote control is fragile — it drops without warning. When it drops, the operator
goes blind. A milestone reached but never pushed is a milestone that might as well
not exist. The pipeline must push results to GitHub autonomously, on schedule, without
human intervention — because the human may not be there. GitHub is not a convenience;
it is the only resilient feedback channel. Everything must flow through it, because
nothing else can be relied on to survive.

## Philosophy 6: Every run is an experiment. Tag it. Keep it. Compare it.

Each training run is an experiment. Experiments are identified by a tag. The tag
scopes every output — plots, results, logs — so no run overwrites another. The
hierarchy is not cosmetic; it is the audit trail. When results appear on GitHub,
the tag tells you exactly which run produced them. If the tag is gone, the
experiment cannot be reconstructed. Never run without a tag. Never reuse a tag.
Never collapse multiple runs into shared folders.

The rule is simple: one tag, one experiment, one set of outputs. Everything else
is noise.
