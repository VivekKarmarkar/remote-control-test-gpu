# Ideas

## Strava overlay with location-aware training events

Overlay training events on a walking route map with clickable icons linking
to GitHub commits. Two types of events need location:

1. **Launch** — when a training run is kicked off from the phone. Can pass
   `--lat` and `--lng` flags to train.py and embed coordinates in commits.

2. **Viewing results** — when plots/results are opened on the phone while
   walking. This is the hard part: GitHub has no location hook.

### Solution: location-aware results page

Instead of viewing raw GitHub commits, host a page (GitHub Pages) that:
- Shows the training plots
- Uses the browser Geolocation API to capture lat/lng and timestamp when
  the page is opened
- Logs where the user was when they viewed each result

Combined with Strava GPS data, this creates a map showing: where runs were
launched, where results were viewed, and the walking route connecting them.
Each marker links to the corresponding GitHub commit.

## Finger-sketch inference on phone

A single HTML page (GitHub Pages) where the user draws a digit with their
finger on a touch-screen canvas. The trained model runs inference in the
browser and shows the prediction.

- HTML5 `<canvas>` with touch events for drawing
- Resize to 28x28, normalize to match MNIST preprocessing
- Model weights exported as JSON (4 weight matrices, 4 bias vectors)
- Inference in plain JavaScript — matrix multiply and ReLU, no ML framework
- Single self-contained HTML file, no server needed

Every sketch-and-predict event also captures location via the browser
Geolocation API.

## The map

All three event types on one map over a walking route:

1. **Launch** — where training was kicked off from the phone
2. **View** — where results were opened and viewed
3. **Sketch** — where a digit was drawn and the model ran inference

Each marker is clickable and links to the corresponding GitHub commit or
prediction result. The whole journey — train, view, interact — on one map.

### Why this matters

The proof is baked into the events themselves — not overlaid after the fact.
The location data comes from the moment of interaction, not from correlating
two separate data sources by timestamp.
