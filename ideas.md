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

### Why this matters

The proof is baked into the events themselves — not overlaid after the fact.
The location data comes from the moment of interaction, not from correlating
two separate data sources by timestamp.
