# GPU Protocol

## Before launching training: disable auto-suspend

The laptop will auto-suspend during training, killing the GPU context and
hanging the process. CUDA cannot recover from suspend — the process stays
alive but spins forever on a GPU call that will never complete.

### Option 1: Per-run inhibit (preferred)

```bash
systemd-inhibit --what=sleep --why="GPU training" .venv/bin/python nn_mnist_gpu.py --tag <tag>
```

### Option 2: Disable sleep system-wide for the session

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target
```

Undo when done:

```bash
sudo systemctl unmask sleep.target suspend.target hibernate.target
```

## After reboot: reload nvidia_uvm

```bash
sudo modprobe nvidia_uvm
```

Verify:

```bash
lsmod | grep nvidia_uvm
```

## If GPU enters fatal error state (Xid 31 / UVM error 0x60)

The kernel will log:

```
NVRM: nvGpuOpsReportFatalError: uvm encountered global fatal error 0x60,
  requiring os reboot to recover.
```

**Only fix: full reboot.** No `modprobe` or module reload will recover from this.
After reboot, run `sudo modprobe nvidia_uvm` again.

## Quick GPU sanity check

```bash
cd "/home/vivekkarmarkar/Python Files/remote-control-test-gpu"
.venv/bin/python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```
