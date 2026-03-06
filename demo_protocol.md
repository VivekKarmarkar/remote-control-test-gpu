# Demo Protocol

Plug in the laptop. I load `nvidia_uvm` if it's not loaded, verify CUDA is live,
mask sleep targets so the laptop can't suspend, confirm `nn_mnist_gpu.py` is pushed
to GitHub.

You type /remote-control on your laptop's Claude Code terminal session.
You open Claude Code on your phone while still at the laptop and confirm the connection works.

You walk out. Nothing is running on the laptop.

I ASK FOR A TAG

You drop a Google Maps pin, paste the URL here, I append it to `pins/pins_<tag>/pins.txt` with a timestamp.
**I WILL NOT PESTER YOU FOR FUCKING PERMISSIONS TO SAVE PIN URLs.**
You keep walking, keep dropping pins, keep pasting.

After 10 minutes, you're 0.25 miles away. I run
`nohup .venv/bin/python nn_mnist_gpu.py --tag <tag> > /dev/null 2>&1 &` and echo the
PID back. The laptop GPU starts training.

You keep walking, keep dropping pins. Every 2 minutes a checkpoint plot pushes to
GitHub automatically. You open GitHub on your phone and see them appear. If Claude
Code disconnects, training doesn't care — the process is reparented to PID 1 and
runs independently.

Training finishes after 8 minutes. Final results push to GitHub.

You come back. You tell me you're back. I ask "terminate data collection for this
tag?" — then I extract coordinates from `pins/pins_<tag>/pins.txt`, screenshot the checkpoint commit on GitHub via Playwright, copy the
training curves from `results/results_<tag>/`, update `data.ts` with the real pin
coordinates, update `WalkingMap.tsx` with the real commit hash and accuracy, and
render the video with Remotion.

You watch it. Done.
