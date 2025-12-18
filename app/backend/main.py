from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from .store import store
from .schemas import (
    PlayerListItem,
    TrajectoryPoint,
    SimilarPlayer,
    LabelResponse,
    LabelSummaryResponse,
    ProjectionPoint,
    RadarResponse,
    CountingGeometryResponse,
)

app = FastAPI(title="NBA Career Analytics")


@app.get("/players", response_model=list[PlayerListItem])
def players():
    return store.players()


@app.get("/player/{player_id}/trajectory", response_model=list[TrajectoryPoint])
def trajectory(player_id: int):
    # Return empty list if no data rather than 404 so UI can show "no seasons" gracefully.
    return store.trajectory(player_id)


@app.get("/player/{player_id}/comps", response_model=list[SimilarPlayer])
def comps(player_id: int, k: int = 3):
    return store.comps(player_id, k)


@app.get("/player/{player_id}/comps_counting", response_model=list[SimilarPlayer])
def comps_counting(player_id: int, k: int = 3):
    try:
        return store.comps_counting(player_id, k)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/player/{player_id}/counting_geometry", response_model=CountingGeometryResponse)
def counting_geometry(player_id: int, k: int = 3):
    try:
        return store.counting_geometry(player_id, k)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/player/{player_id}/label", response_model=LabelResponse)
def label(player_id: int):
    return store.label(player_id)


@app.get("/labels/summary", response_model=LabelSummaryResponse)
def labels_summary():
    return store.label_summary()


@app.get("/player/{player_id}/projection", response_model=list[ProjectionPoint])
def projection(player_id: int):
    return store.projection(player_id)


@app.get("/player/{player_id}/radar", response_model=RadarResponse)
def radar(player_id: int, k: int = 3):
    return store.radar(player_id, k)


@app.get("/", response_class=HTMLResponse)
def index():
    # Simple HTML that consumes the API and renders a dropdown + results.
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>NBA Career Analytics</title>
      <style>
        body { font-family: sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }
        h1 { margin-bottom: 0.5rem; }
        select, button { padding: 0.35rem 0.5rem; font-size: 1rem; }
        pre { background: #111; color: #f5f5f5; padding: 1rem; border-radius: 8px; overflow-x: auto; }
        .row { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 0.75rem; margin-top: 1rem; }
      </style>
    </head>
    <body>
      <h1>NBA Career Analytics</h1>
      <div class="row">
        <label for="player">Player:</label>
        <select id="player"></select>
        <button id="load">Load</button>
      </div>
      <div class="card">
        <h3>Label</h3>
        <div id="label">—</div>
      </div>
      <div class="card">
        <h3>Trajectory (raw)</h3>
        <pre id="traj">[]</pre>
      </div>
      <div class="card">
        <h3>Similar Players</h3>
        <pre id="comps">[]</pre>
      </div>
      <div class="card">
        <h3>Projection</h3>
        <pre id="proj">[]</pre>
      </div>
      <script>
        const playerSelect = document.getElementById("player");
        const loadBtn = document.getElementById("load");
        const labelDiv = document.getElementById("label");
        const trajPre = document.getElementById("traj");
        const compsPre = document.getElementById("comps");
        const projPre = document.getElementById("proj");

        async function fetchPlayers() {
          const res = await fetch("/players");
          const data = await res.json();
          playerSelect.innerHTML = data
            .map(p => `<option value="${p.player_id}">${p.name} (${p.from_year}-${p.to_year})</option>`)
            .join("");
        }

        async function loadPlayer() {
          const id = playerSelect.value;
          if (!id) return;
          const [traj, comps, label, proj] = await Promise.all([
            fetch(`/player/${id}/trajectory`).then(r => r.json()),
            fetch(`/player/${id}/comps`).then(r => r.json()),
            fetch(`/player/${id}/label`).then(r => r.json()),
            fetch(`/player/${id}/projection`).then(r => r.json()),
          ]);
          labelDiv.textContent = label.label || "—";
          trajPre.textContent = JSON.stringify(traj, null, 2);
          compsPre.textContent = JSON.stringify(comps, null, 2);
          projPre.textContent = JSON.stringify(proj, null, 2);
        }

        loadBtn.addEventListener("click", loadPlayer);
        fetchPlayers().then(() => loadPlayer());
      </script>
    </body>
    </html>
    """
