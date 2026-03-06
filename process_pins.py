"""Process pin drop data from a demo run.

Reads pins/pins_{tag}/pins.txt, resolves Google Maps short URLs to
lat/lng coordinates, and generates:
  1. Coordinates printed to stdout (for data.ts)
  2. walking_route.html — interactive Leaflet map with animated walker
  3. walking_route.png — static matplotlib plot on satellite-style background

Usage:
    .venv/bin/python process_pins.py --tag demorun2
    .venv/bin/python process_pins.py --tag demorun2 --commits 5283d13,21da022,b420a34,cb5d95e,00a9e3f --launch-pin 5
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def git_push_pins(pins_path: Path, tag: str):
    """Commit and push the pins data to git."""
    project_root = pins_path.parent.parent.parent  # pins/pins_{tag}/pins.txt → root
    pins_rel = str(pins_path.relative_to(project_root))

    try:
        subprocess.run(['git', 'add', pins_rel], check=True, capture_output=True, cwd=project_root)
        # Check if there's anything to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True, cwd=project_root)
        if result.returncode == 0:
            print(f'  [git] pins already committed, skipping', file=sys.stderr)
            return
        subprocess.run(
            ['git', 'commit', '-m', f'pin drops [{tag}]'],
            check=True, capture_output=True, cwd=project_root,
        )
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            check=True, capture_output=True, timeout=30, cwd=project_root,
        )
        print(f'  [git] pushed: pin drops [{tag}]', file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f'  [git] push failed: {e}', file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f'  [git] push timed out', file=sys.stderr)


def resolve_pin_url(url: str) -> tuple[float, float] | None:
    """Resolve a Google Maps short URL to (lat, lng) coordinates."""
    try:
        result = subprocess.run(
            ['curl', '-sIL', url],
            capture_output=True, text=True, timeout=15,
        )
        headers = result.stdout
        # Find the final Location header with coordinates
        for line in headers.split('\n'):
            if 'location:' in line.lower() and ('maps.google.com' in line or 'google.com/maps' in line):
                # Extract !3d (lat) and !4d (lng) from URL
                lat_match = re.search(r'!3d(-?[\d.]+)', line)
                lng_match = re.search(r'!4d(-?[\d.]+)', line)
                if lat_match and lng_match:
                    return float(lat_match.group(1)), float(lng_match.group(1))
                # Try @lat,lng pattern
                at_match = re.search(r'@(-?[\d.]+),(-?[\d.]+)', line)
                if at_match:
                    return float(at_match.group(1)), float(at_match.group(2))
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f'  Warning: failed to resolve {url}: {e}', file=sys.stderr)
    return None


def parse_pins_file(pins_path: Path) -> list[dict]:
    """Parse pins.txt → list of {time, url} dicts."""
    pins = []
    for line in pins_path.read_text().strip().split('\n'):
        parts = line.strip().split()
        if len(parts) >= 2:
            pins.append({'time': parts[0], 'url': parts[1]})
    return pins


def resolve_all_pins(pins: list[dict]) -> list[dict]:
    """Resolve all pin URLs to coordinates."""
    resolved = []
    for i, pin in enumerate(pins):
        print(f'  Resolving pin {i + 1}/{len(pins)}...', file=sys.stderr)
        coords = resolve_pin_url(pin['url'])
        if coords:
            resolved.append({
                'lat': round(coords[0], 5),
                'lng': round(coords[1], 5),
                'time': pin['time'],
                'label': 'Start' if i == 0 else ('End' if i == len(pins) - 1 else f'Pin {i + 1}'),
            })
        else:
            print(f'  ERROR: Could not resolve pin {i + 1}: {pin["url"]}', file=sys.stderr)
    return resolved


def print_data_ts(pins: list[dict]):
    """Print pin data in data.ts format."""
    print('\n// Pin data — paste into walking-video/src/data.ts')
    print('export const pins = [')
    for pin in pins:
        print(f"  {{lat: {pin['lat']}, lng: {pin['lng']}, time: '{pin['time']}', label: '{pin['label']}'}},")
    print('];')


def generate_html(pins: list[dict], commits: list[dict], launch_pin: int | None, output_path: Path):
    """Generate interactive walking_route.html."""
    center_lat = sum(p['lat'] for p in pins) / len(pins)
    center_lng = sum(p['lng'] for p in pins) / len(pins)

    # Build pins JS array
    pins_js = ',\n    '.join(
        f"{{lat: {p['lat']}, lng: {p['lng']}, time: '{p['time'][11:16] if 'T' in p['time'] else p['time']}', label: '{p['label']}'}}"
        for p in pins
    )

    # Build commits JS array
    commits_js = ''
    if commits:
        commit_entries = []
        for c in commits:
            commit_entries.append(
                f"    {{\n"
                f"        hash: '{c['hash']}', label: '{c['label']}',\n"
                f"        lat: {c['lat']}, lng: {c['lng']},\n"
                f"        url: '{c['url']}',\n"
                f"    }}"
            )
        commits_js = ',\n'.join(commit_entries)

    # Launch pin JS
    launch_js = ''
    launch_legend = ''
    launch_marker = ''
    if launch_pin is not None and 0 < launch_pin <= len(pins):
        lp = pins[launch_pin - 1]
        launch_js = f"const launchPin = {{lat: {lp['lat']}, lng: {lp['lng']}}};"
        launch_legend = '<div style="margin-top: 4px;">&#11088; Training launched from phone</div>'
        launch_marker = """
// ── Launch marker ────────────────────────────────────────────────────
const launchIcon = L.divIcon({
    html: '<div style="font-size: 36px; text-align: center; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.7));">⭐</div>',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    className: '',
});
const launchMarkerEl = L.marker([launchPin.lat, launchPin.lng], {icon: launchIcon, zIndexOffset: 900}).addTo(map);
launchMarkerEl.bindPopup(`
    <div class="commit-popup">
        <b>Training launched</b><br>
        <span style="color: #888;">Fired from phone</span>
    </div>
`, {maxWidth: 280});
"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Walking Route — Iowa City</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css" />
    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js"></script>
    <style>
        html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
        #map {{ position: absolute; inset: 0; }}
        .header {{
            position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000;
            background: rgba(0,0,0,0.85); color: white; padding: 14px 28px; border-radius: 10px;
            font-family: sans-serif; font-size: 15px; font-weight: bold; text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        .header small {{ font-weight: normal; font-size: 12px; color: #aaa; }}
        .legend {{
            position: fixed; bottom: 20px; left: 14px; z-index: 1000;
            background: rgba(0,0,0,0.85); color: white; padding: 12px 16px; border-radius: 8px;
            font-family: sans-serif; font-size: 12px; line-height: 1.8;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        .legend-dot {{
            display: inline-block; width: 10px; height: 10px; border-radius: 50%;
            margin-right: 6px; vertical-align: middle;
        }}
        .commit-popup {{ font-family: sans-serif; text-align: center; line-height: 1.6; }}
        .commit-popup b {{ font-size: 13px; }}
        .commit-popup code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
        .commit-popup a {{ color: #0074D9; font-weight: bold; text-decoration: none; }}
        .commit-popup a:hover {{ text-decoration: underline; }}
        .pin-popup {{ font-family: sans-serif; font-size: 13px; }}
        .walker-dot {{
            width: 18px; height: 18px; border-radius: 50%;
            background: #2ECC40; border: 3px solid white;
            box-shadow: 0 0 12px rgba(46, 204, 64, 0.6);
        }}
        .walker-pulse {{ animation: pulse 1.5s ease-in-out infinite; }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 12px rgba(46, 204, 64, 0.6); }}
            50% {{ box-shadow: 0 0 24px rgba(46, 204, 64, 0.9); }}
        }}
        .playback {{
            position: fixed; bottom: 20px; right: 14px; z-index: 1000;
            background: rgba(0,0,0,0.85); color: white; padding: 10px 16px; border-radius: 8px;
            font-family: sans-serif; font-size: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            display: flex; align-items: center; gap: 10px;
        }}
        .playback button {{
            background: #2ECC40; color: white; border: none; border-radius: 6px;
            padding: 6px 14px; cursor: pointer; font-size: 13px; font-weight: bold;
        }}
        .playback button:hover {{ background: #27ae60; }}
        .playback button.paused {{ background: #FF851B; }}
        .playback-time {{ min-width: 80px; text-align: center; font-variant-numeric: tabular-nums; }}
    </style>
</head>
<body>

<div class="header">
    Walking Route — Iowa City
    <br><small>Click the phone emojis to view git commits pushed while walking</small>
</div>

<div class="legend">
    <div><span class="legend-dot" style="background:#2ECC40;"></span> Start</div>
    <div><span class="legend-dot" style="background:#FF4136;"></span> End</div>
    <div><span class="legend-dot" style="background:#0074D9;"></span> Pin drop (every 2 min)</div>
    {launch_legend}
    <div>&#128241; Git commit pushed while walking</div>
</div>

<div class="playback">
    <button id="playBtn" onclick="togglePlay()">&#9654; Play</button>
    <span class="playback-time" id="timeLabel"></span>
    <input type="range" id="scrubber" min="0" max="1000" value="0" style="width: 140px; cursor: pointer;"
           oninput="scrub(this.value)">
    <span style="color: #aaa;">&times;</span>
    <select id="speedSelect" onchange="setSpeed(this.value)" style="background: #333; color: white; border: 1px solid #555; border-radius: 4px; padding: 2px;">
        <option value="1">1&times;</option>
        <option value="2" selected>2&times;</option>
        <option value="4">4&times;</option>
        <option value="8">8&times;</option>
    </select>
</div>

<div id="map"></div>

<script>
const pins = [
    {pins_js}
];

const commits = [
{commits_js}
];

{launch_js}

const center = [
    pins.reduce((s, p) => s + p.lat, 0) / pins.length,
    pins.reduce((s, p) => s + p.lng, 0) / pins.length,
];

const map = L.map('map', {{center, zoom: 17, zoomControl: true}});

L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
    maxZoom: 20, attribution: 'Google Satellite',
}}).addTo(map);

const routeCoords = pins.map(p => [p.lat, p.lng]);
L.polyline(routeCoords, {{
    color: '#FF4136', weight: 5, opacity: 0.9,
    lineCap: 'round', lineJoin: 'round',
}}).addTo(map);

pins.forEach((pin, i) => {{
    const isStart = i === 0;
    const isEnd = i === pins.length - 1;
    const marker = L.circleMarker([pin.lat, pin.lng], {{
        radius: (isStart || isEnd) ? 10 : 6,
        fillColor: isStart ? '#2ECC40' : (isEnd ? '#FF4136' : '#0074D9'),
        color: 'white', weight: (isStart || isEnd) ? 3 : 2,
        fillOpacity: (isStart || isEnd) ? 1 : 0.9,
    }}).addTo(map);
    marker.bindPopup('<div class="pin-popup"><b>' + pin.label + '</b><br>' + pin.time + '</div>');
}});

commits.forEach(commit => {{
    const icon = L.divIcon({{
        html: '<div style="font-size: 26px; text-align: center; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">&#128241;</div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        className: '',
    }});
    const marker = L.marker([commit.lat, commit.lng], {{icon}}).addTo(map);
    marker.bindPopup(
        '<div class="commit-popup"><b>' + commit.label + '</b><br>' +
        '<code>' + commit.hash + '</code><br>' +
        '<a href="' + commit.url + '" target="_blank">View commit on GitHub &rarr;</a></div>',
        {{maxWidth: 250}}
    );
}});

{launch_marker}

map.fitBounds(L.polyline(routeCoords).getBounds().pad(0.1));

// ── Animated walker ──────────────────────────────────────────────────
function lerp(a, b, t) {{ return a + (b - a) * t; }}

const segDists = [];
let totalDist = 0;
for (let i = 1; i < routeCoords.length; i++) {{
    totalDist += map.distance(routeCoords[i - 1], routeCoords[i]);
    segDists.push(totalDist);
}}

function posAtProgress(progress) {{
    const targetDist = progress * totalDist;
    if (progress <= 0) return routeCoords[0];
    if (progress >= 1) return routeCoords[routeCoords.length - 1];
    for (let i = 0; i < segDists.length; i++) {{
        const segStart = i === 0 ? 0 : segDists[i - 1];
        if (targetDist <= segDists[i]) {{
            const segT = (targetDist - segStart) / (segDists[i] - segStart);
            return [
                lerp(routeCoords[i][0], routeCoords[i + 1][0], segT),
                lerp(routeCoords[i][1], routeCoords[i + 1][1], segT),
            ];
        }}
    }}
    return routeCoords[routeCoords.length - 1];
}}

const walkEndMin = (pins.length - 1) * 2;

function progressToTime(progress) {{
    const startParts = pins[0].time.split(':');
    const startH = parseInt(startParts[0]);
    const startM = parseInt(startParts[1]);
    const totalMin = startM + progress * walkEndMin;
    const h = startH + Math.floor(totalMin / 60);
    const m = Math.floor(totalMin % 60);
    return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
}}

const walkerIcon = L.divIcon({{
    html: '<div class="walker-dot walker-pulse"></div>',
    iconSize: [24, 24], iconAnchor: [12, 12], className: '',
}});
const walkerMarker = L.marker(routeCoords[0], {{icon: walkerIcon, zIndexOffset: 1000}}).addTo(map);

const trail = L.polyline([], {{
    color: '#2ECC40', weight: 3, opacity: 0.7,
    lineCap: 'round', lineJoin: 'round',
}}).addTo(map);

let playing = false, progress = 0, speed = 2, lastTimestamp = null;

function updateWalker(p) {{
    progress = Math.max(0, Math.min(1, p));
    const pos = posAtProgress(progress);
    walkerMarker.setLatLng(pos);
    const trailCoords = [routeCoords[0]];
    const targetDist = progress * totalDist;
    for (let i = 0; i < segDists.length; i++) {{
        if (segDists[i] <= targetDist) trailCoords.push(routeCoords[i + 1]);
        else {{ trailCoords.push(pos); break; }}
    }}
    trail.setLatLngs(trailCoords);
    document.getElementById('timeLabel').textContent = progressToTime(progress);
    document.getElementById('scrubber').value = Math.round(progress * 1000);
}}

function animate(timestamp) {{
    if (!playing) return;
    if (lastTimestamp === null) lastTimestamp = timestamp;
    const dt = timestamp - lastTimestamp;
    lastTimestamp = timestamp;
    progress += dt * speed / (walkEndMin * 1000);
    if (progress >= 1) {{
        progress = 1; playing = false;
        document.getElementById('playBtn').innerHTML = '&#8634; Replay';
        document.getElementById('playBtn').className = '';
    }}
    updateWalker(progress);
    if (playing) requestAnimationFrame(animate);
}}

function togglePlay() {{
    const btn = document.getElementById('playBtn');
    if (progress >= 1) {{
        progress = 0; playing = true; lastTimestamp = null;
        btn.innerHTML = '&#9208; Pause'; btn.className = 'paused';
        requestAnimationFrame(animate);
    }} else if (playing) {{
        playing = false; lastTimestamp = null;
        btn.innerHTML = '&#9654; Play'; btn.className = '';
    }} else {{
        playing = true; lastTimestamp = null;
        btn.innerHTML = '&#9208; Pause'; btn.className = 'paused';
        requestAnimationFrame(animate);
    }}
}}

function scrub(val) {{
    playing = false; lastTimestamp = null;
    updateWalker(val / 1000);
    document.getElementById('playBtn').innerHTML = '&#9654; Play';
    document.getElementById('playBtn').className = '';
}}

function setSpeed(val) {{ speed = parseFloat(val); }}

updateWalker(0);
</script>
</body>
</html>"""

    output_path.write_text(html)
    print(f'  HTML → {output_path}', file=sys.stderr)


def generate_png(pins: list[dict], output_path: Path):
    """Generate a static walking_route.png with matplotlib."""
    lats = [p['lat'] for p in pins]
    lngs = [p['lng'] for p in pins]

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.plot(lngs, lats, '-', color='#FF4136', linewidth=2.5, zorder=2)
    ax.scatter(lngs[1:-1], lats[1:-1], c='#0074D9', s=30, zorder=3, edgecolors='white', linewidths=0.5)
    ax.scatter([lngs[0]], [lats[0]], c='#2ECC40', s=100, zorder=4, edgecolors='white', linewidths=2, label='Start')
    ax.scatter([lngs[-1]], [lats[-1]], c='#FF4136', s=100, zorder=4, edgecolors='white', linewidths=2, marker='s', label='End')

    for i, pin in enumerate(pins):
        if i == 0 or i == len(pins) - 1:
            ax.annotate(pin['label'], (pin['lng'], pin['lat']),
                       textcoords='offset points', xytext=(8, 8),
                       fontsize=8, fontweight='bold', color='white',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))

    ax.set_facecolor('#2d3436')
    fig.patch.set_facecolor('#2d3436')
    ax.tick_params(colors='white', labelsize=7)
    for spine in ax.spines.values():
        spine.set_color('#555')
    ax.set_xlabel('Longitude', color='white', fontsize=9)
    ax.set_ylabel('Latitude', color='white', fontsize=9)
    ax.set_title('Walking Route — Iowa City', color='white', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8, facecolor='#2d3436', edgecolor='#555',
              labelcolor='white')
    ax.set_aspect('equal')

    plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f'  PNG → {output_path}', file=sys.stderr)


def parse_commits_arg(commits_str: str, pins: list[dict], launch_pin: int) -> list[dict]:
    """Parse comma-separated commit hashes and position them relative to pins.

    Commits are checkpoint plots pushed every 2 minutes after training launch.
    Position: launch_pin + (i+1) for each checkpoint, interpolated for final results.
    """
    hashes = [h.strip() for h in commits_str.split(',')]
    repo_url = 'https://github.com/VivekKarmarkar/remote-control-test-gpu/commit'
    result = []
    for i, h in enumerate(hashes):
        is_final = (i == len(hashes) - 1 and 'final' not in h)
        # Checkpoints land on pins: launch_pin + (i+1) * 1 pin per 2-min checkpoint
        pin_idx = launch_pin - 1 + (i + 1)  # 0-indexed

        if pin_idx >= len(pins):
            # Past end of route — clamp to last pin
            pin_idx = len(pins) - 1

        if is_final or i == len(hashes) - 1:
            # Final results: interpolate between this pin and next
            next_idx = min(pin_idx + 1, len(pins) - 1)
            lat = (pins[pin_idx]['lat'] + pins[next_idx]['lat']) / 2
            lng = (pins[pin_idx]['lng'] + pins[next_idx]['lng']) / 2
            label = 'final results' if i == len(hashes) - 1 else f'checkpoint {(i + 1) * 2}min'
        else:
            lat = pins[pin_idx]['lat']
            lng = pins[pin_idx]['lng']
            label = f'checkpoint {(i + 1) * 2}min'

        result.append({
            'hash': h,
            'label': label,
            'lat': lat,
            'lng': lng,
            'url': f'{repo_url}/{h}',
        })
    return result


def main():
    parser = argparse.ArgumentParser(description='Process pin drop data from a demo run')
    parser.add_argument('--tag', required=True, help='Demo run tag (e.g., demorun2)')
    parser.add_argument('--commits', help='Comma-separated commit hashes (checkpoint order)')
    parser.add_argument('--launch-pin', type=int, help='Pin number where training was launched')
    parser.add_argument('--skip-resolve', action='store_true',
                       help='Skip URL resolution, use pre-resolved coords from data.ts')
    args = parser.parse_args()

    project_root = Path(__file__).parent
    pins_path = project_root / 'pins' / f'pins_{args.tag}' / 'pins.txt'

    if not pins_path.exists():
        print(f'ERROR: {pins_path} not found', file=sys.stderr)
        sys.exit(1)

    print(f'Processing pins for tag: {args.tag}', file=sys.stderr)

    # Commit and push pins data first
    git_push_pins(pins_path, args.tag)

    # Parse and resolve pins
    raw_pins = parse_pins_file(pins_path)
    print(f'  Found {len(raw_pins)} pins', file=sys.stderr)

    if args.skip_resolve:
        print('  Skipping URL resolution (use --commits with pre-resolved data)', file=sys.stderr)
        return

    pins = resolve_all_pins(raw_pins)
    if not pins:
        print('ERROR: No pins could be resolved', file=sys.stderr)
        sys.exit(1)

    print(f'  Resolved {len(pins)}/{len(raw_pins)} pins', file=sys.stderr)

    # Print data.ts format
    print_data_ts(pins)

    # Parse commits if provided
    commits = []
    if args.commits and args.launch_pin:
        commits = parse_commits_arg(args.commits, pins, args.launch_pin)

    # Generate outputs
    generate_html(pins, commits, args.launch_pin, project_root / 'walking_route.html')
    generate_png(pins, project_root / 'walking_route.png')

    # Commit and push generated outputs
    try:
        subprocess.run(['git', 'add', 'walking_route.html', 'walking_route.png'],
                      check=True, capture_output=True, cwd=project_root)
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True, cwd=project_root)
        if result.returncode != 0:
            subprocess.run(
                ['git', 'commit', '-m', f'walking route map and plot [{args.tag}]'],
                check=True, capture_output=True, cwd=project_root,
            )
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                check=True, capture_output=True, timeout=30, cwd=project_root,
            )
            print(f'  [git] pushed: walking route outputs [{args.tag}]', file=sys.stderr)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f'  [git] output push failed: {e}', file=sys.stderr)

    print(f'\nDone. {len(pins)} pins processed.', file=sys.stderr)


if __name__ == '__main__':
    main()
