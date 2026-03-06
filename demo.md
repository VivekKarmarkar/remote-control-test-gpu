# Demo Video

An 18-second animated video that proves the magic moment happened.

## The story in three beats

1. **Phone icon** — "Claude pushed from the laptop / Git is the messenger"
2. **GitHub commit** — "Phone sees it on GitHub — commit XXXXXXX"
3. **Training curves** — "Laptop GPU trained to XX.X% accuracy"

Satellite flyover of the actual walking route, green dot moving, red trail
drawing behind it. The overlays emerge mid-walk and fade back to the map.

## Ingredients

### Collected during the walk

| Ingredient | How | Stored |
|---|---|---|
| Pin drop URLs | User drops Google Maps pins, pastes URLs into Claude Code | `pins.txt` — one URL per line, timestamp prepended |
| Training run | `nohup .venv/bin/python nn_mnist_gpu.py --tag <tag>` launched from phone | Checkpoint plots auto-push to GitHub every 2 min |

`pins.txt` format — Claude appends each URL as it arrives, no processing:
```
2026-03-06T03:12:00Z https://maps.app.goo.gl/XXXXX
2026-03-06T03:15:30Z https://maps.app.goo.gl/YYYYY
2026-03-06T03:18:45Z https://maps.app.goo.gl/ZZZZZ
```

Nothing else happens during the walk. No curl, no git from Claude's side,
no coordinate extraction. Just append URLs to a text file. The training run
pushes its own checkpoints independently.

### Collected after the walk

| Ingredient | How | Stored |
|---|---|---|
| Pin coordinates | Batch `curl -sIL` on every URL in `pins.txt`, extract lat/lng from redirect | `walking-video/src/data.ts` |
| GitHub commit screenshot | Playwright navigates to the commit page, takes a 1280x800 screenshot | `walking-video/public/github-commit.png` |
| Training curves plot | Copy from `results/results_<tag>/01_training_curves.png` | `walking-video/public/training-curves.png` |
| Commit hash + metadata | Read from git log | `walking-video/src/data.ts` |

### Already built (the pipeline)

| Component | Path |
|---|---|
| Remotion project | `walking-video/` |
| Map component | `walking-video/src/WalkingMap.tsx` |
| Composition config | `walking-video/src/Root.tsx` |
| Data template | `walking-video/src/data.ts` |
| Mapbox token | `walking-video/.env` (gitignored) |

## Recipe

### Pre-walk

1. `sudo modprobe nvidia_uvm` (if needed)
2. Verify CUDA: `.venv/bin/python -c "import torch; print(torch.cuda.is_available())"`
3. Disable laptop sleep
4. Confirm `nn_mnist_gpu.py` is ready

### During the walk

**Critical ordering: walk first, launch second.**

At 1.5 mph, checkpoint 1 fires at T_launch + 120s — only 0.05 miles from the laptop.
Training ends at T_launch + 480s — only ~0.2 miles away. The demo only works if
T_launch happens after you are already ≥0.25 miles from the laptop.

1. Leave the laptop. Drop a Google Maps pin at the starting point.
2. Paste the URL into Claude Code — Claude appends to `pins.txt`, nothing else.
3. Walk. Drop more pins as you go.
4. Once you are ≥0.25 miles from the laptop (~10 min at 1.5 mph), **launch training**
   from the phone via Claude Code:
   ```
   nohup .venv/bin/python nn_mnist_gpu.py --tag <tag> > /dev/null 2>&1 &
   echo "PID: $!"
   ```
5. Keep walking. Drop more pins.
6. Monitor GitHub — checkpoint plots appear every 2 min while you are genuinely far away.
7. Return whenever you like. Training runs for 8 min total and exits cleanly.

### After the walk

1. **Extract coordinates** — batch-process `pins.txt`:
   ```bash
   while IFS=' ' read -r ts url; do
     coords=$(curl -sIL "$url" 2>/dev/null | grep -i location | tail -1 | grep -oP '[\d.-]+,[\d.-]+')
     echo "$ts $coords"
   done < pins.txt > pin_coords.txt
   ```

2. **Update data.ts** — replace pin array with real coordinates and timestamps

3. **Screenshot the commit** — Playwright captures the real commit page:
   ```
   walking-video/public/github-commit.png
   ```

4. **Copy training curves** — from the real run:
   ```bash
   cp results/results_<tag>/01_training_curves.png walking-video/public/training-curves.png
   ```

5. **Update labels** — real commit hash, real accuracy number in WalkingMap.tsx

6. **Render**:
   ```bash
   cd walking-video
   npx remotion render WalkingRoute --output=walking-route.mp4
   ```

## What the video proves

- The walking route is real (satellite imagery + GPS coordinates from pin drops)
- The commit is real (GitHub screenshot with timestamp, author, diff)
- The training is real (loss and accuracy curves from the actual GPU run)
- Git is the messenger — laptop Claude pushes, the phone sees it
