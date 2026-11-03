# Day 19 - 3-minute live demo script

**Before you start (2 min):** run `run.ps1`, open http://127.0.0.1:8000/compare.html, full-screen the browser,
set speed to 2x, click **Reset roads**, zoom so the whole network is visible. Pick your start/end pair in advance:
choose two junctions on opposite sides of the map and **test that blocking one road on the route still leaves a detour**.

| Time | Action | Say |
|---|---|---|
| 0:00 | Show the two empty maps | "The network has N real junctions from OpenStreetMap, stored as a weighted directed graph. Left is Dijkstra, right is A*. Same graph, same query." |
| 0:20 | Click a start junction, then an end junction | "I select an origin and a destination. Green is the start, red is the end." |
| 0:35 | Press **Run both** and let it play | "Watch the search frontier. Dijkstra spreads in every direction because it has no idea where the goal is. A* is pulled toward the target by the Haversine heuristic." |
| 1:15 | Animation ends; point at the HUDs and the blue bar | "Both find the same optimal route, because the heuristic is admissible. A* explored X nodes against Dijkstra's Y: Z% fewer. That is less CPU and less memory for the same answer." |
| 1:50 | Click a road on the blue route, choose **Block road** | "Now a road closes. The server sets that edge's cost to infinity - no graph rebuild - and recomputes." |
| 2:00 | The search replays automatically | "Both algorithms re-route around the closure; the route length changed from A to B km." |
| 2:30 | Click another road, **Heavy traffic (x3)**, switch objective to **Fastest time**, Run both | "In time mode congestion multiplies the cost, so traffic changes the route even without a closure." |
| 2:50 | Close | "Complexity is O((V+E) log V) with an indexed binary heap, and A* stays optimal because h(n) never overestimates. Happy to take questions." |

## If something goes wrong
- Page blank or "Cannot reach the API server": uvicorn is not running. Start it with `run.ps1`.
- Map tiles missing (no internet): the graph still draws; carry on, or switch to the backup video.
- Blocking a road leaves **no** route: say "this closure disconnects the network - the system reports it rather than crashing", then press **Reset roads**.

## Day 19 recording (backup video)
- Windows: **OBS Studio** -> Settings -> Video: Base/Output 1920x1080, **FPS 60**; Output: MP4 (or MKV then remux), bitrate 12000+ Kbps; source = "Window Capture" of the browser.
  Quick alternative: **Win + Alt + R** (Xbox Game Bar) records the active window.
- Do the full script once in one take, narrate live. Save as `docs/demo_backup.mp4` (keep it out of git if > 100 MB; put it on Drive/USB instead).
- Test the file on another computer and copy it to a USB stick.
