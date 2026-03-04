# Debugging

## Debug 1: trialrun4b hang (March 3, 2026)

### The issue

trialrun4b was launched from phone via remote control. The process ran for
1 hour 27 minutes but only completed ~6 minutes of actual training (84 epochs,
382.6 seconds). GPU utilization was 0%, process state was R (running) on CPU,
37 threads. No errors in the log — it just stopped producing output after
epoch 84.

### Initial investigation

Checked the process state, log tail, GPU utilization, file descriptors,
process tree. Found the process was alive but not making progress. Identified
that GPU was idle (0% utilization) while the CPU was spinning. Could not
determine the root cause from surface-level checks alone.

### The pivot: parallel agent investigation

The user directed sending a team of agents to investigate, for two specific
reasons:

1. **Unbiased** — fresh agents with no prior assumptions would look at the
   evidence without anchoring to hypotheses already forming in the main
   session. A single investigator tends to fixate on their first theory.
   Multiple independent agents each start from scratch.

2. **Parallelized work leading to efficiency + accuracy** — four independent
   investigations running simultaneously cover more ground faster than one
   sequential investigation. Each agent focuses on one domain without
   context-switching. Results cross-validate each other.

### The agents

| Agent | Domain | Key finding |
|-------|--------|-------------|
| Log analysis | Compare all 5 training run logs | trialrun4b is the only run that didn't finish. Hang was during training, not during git or plotting. |
| Code analysis | Threading, TeeLogger, CUDA, deadlocks | Ranked CUDA driver hang as #1 hypothesis. 37 threads is normal PyTorch behavior, not resource exhaustion. |
| Git investigation | Commit history, lock files, cross-process conflicts | Git was clean. No overlapping commits, no lock files, no cross-process issues. |
| System investigation | Kernel logs, suspend/resume, GPU state | **Found the root cause.** |

### Root cause

The system agent found multiple suspend/resume cycles in the kernel logs. The
laptop auto-suspended at 17:49:41 — approximately 6 minutes into trialrun4b's
training. It resumed 1 hour 18 minutes later at 19:07:45.

When the laptop suspends during GPU training:
- GPU context is invalidated (CUDA memory mappings torn down)
- The Python process stays alive but spins on a CUDA call that will never complete
- GPU utilization drops to 0%
- The CUDA context is irrecoverably broken on resume

After the hang, a `modprobe` attempt triggered a fatal Xid 31 MMU page fault
(UVM error 0x60), requiring a full reboot to recover.

### Fix

Documented in `gpu_protocol.md`. Disable auto-suspend before launching
training using `systemd-inhibit` or by masking sleep targets.
