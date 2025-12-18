import { useEffect, useMemo, useState } from "react";
import { fetchPlayers, fetchTrajectory, fetchComps, fetchLabel, fetchProjection, fetchRadar } from "./lib/api";
import PlayerSelector from "./components/PlayerSelector";
import SimilarList from "./components/SimilarList";
import LabelCard from "./components/LabelCard";
import ProjectionTable from "./components/ProjectionTable";
import CareerChart from "./components/CareerChart";
import ProfileCard from "./components/ProfileCard";
import RadarChart from "./components/RadarChart";

type TrajectoryPoint = {
  season: number;
  age: number | null;
  gp: number;
  mpg: number | null;
  pts_per_game: number | null;
  ast_per_game: number | null;
  reb_per_game: number | null;
  fg3_per_game: number | null;
  fg_pct: number | null;
  ft_pct: number | null;
  stl_per_game: number | null;
  blk_per_game: number | null;
  tov_per_game: number | null;
  ts_pct: number | null;
  annotation: string | null;
  value_score?: number | null;
};

function formatPct(v: number | null | undefined) {
  if (v === null || v === undefined) return "—";
  return (v * 100).toFixed(1) + "%";
}

export default function App() {
  const [players, setPlayers] = useState<any[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [seasonFilter, setSeasonFilter] = useState<number | "all">("all");
  const maxUiSeason = 2024;
  const selectedPlayer = useMemo(
    () => players.find((p) => p.player_id === selected),
    [players, selected]
  );
  const [trajectory, setTrajectory] = useState<TrajectoryPoint[]>([]);
  const [comps, setComps] = useState<any[]>([]);
  const [label, setLabel] = useState<string>("");
  const [projection, setProjection] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const has2024Season = trajectory.some((t) => t.season === 2024 && (t.gp ?? 0) > 0);
  const [radar, setRadar] = useState<{ series: any[] }>({ series: [] });

  const eligiblePlayers = useMemo(() => {
    return players.filter((p) => {
      const count = typeof p.season_count === "number" ? p.season_count : null;
      if (count !== null && !Number.isNaN(count)) {
        return count >= 3;
      }
      if (p.from_year != null && p.to_year != null) {
        return p.to_year - p.from_year + 1 >= 3;
      }
      return false;
    });
  }, [players]);

  const seasonOptions = useMemo(() => {
    const seasons = new Set<number>();
    players.forEach((p) => {
      const played: unknown = p.seasons_played;
      if (Array.isArray(played)) {
        played.forEach((s) => typeof s === "number" && s <= maxUiSeason && seasons.add(s));
      } else if (p.from_year != null && p.to_year != null) {
        for (let y = Number(p.from_year); y <= Math.min(Number(p.to_year), maxUiSeason); y++) {
          if (!Number.isNaN(y)) seasons.add(y);
        }
      }
    });
    return Array.from(seasons).sort((a, b) => b - a);
  }, [players, maxUiSeason]);

  const filteredPlayers = useMemo(() => {
    if (seasonFilter === "all") return eligiblePlayers;
    return eligiblePlayers.filter((p) => {
      const played: unknown = p.seasons_played;
      if (Array.isArray(played)) return played.includes(seasonFilter);
      if (p.from_year != null && p.to_year != null) {
        return Number(p.from_year) <= seasonFilter && Math.min(Number(p.to_year), maxUiSeason) >= seasonFilter;
      }
      return false;
    });
  }, [eligiblePlayers, seasonFilter, maxUiSeason]);

  useEffect(() => {
    if (!filteredPlayers.length) return;
    if (selected && filteredPlayers.some((p) => p.player_id === selected)) return;
    setSelected(filteredPlayers[0].player_id);
  }, [filteredPlayers, selected]);


  useEffect(() => {
    fetchPlayers()
      .then((list) => {
        setPlayers(list);
        const firstEligible = list.find((p: any) => {
          const count = typeof p.season_count === "number" ? p.season_count : null;
          if (count !== null && !Number.isNaN(count)) return count >= 3;
          if (p.from_year != null && p.to_year != null) return p.to_year - p.from_year + 1 >= 3;
          return false;
        });
        if (firstEligible) setSelected(firstEligible.player_id);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchTrajectory(selected),
      fetchComps(selected),
      fetchLabel(selected),
      fetchProjection(selected),
    ])
      .then(([traj, compList, lbl, proj]) => {
        setTrajectory(traj);
        setComps(compList);
        setLabel(lbl?.label || "—");
        setProjection(proj);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    // Fetch radar separately so it doesn't block the main data.
    fetchRadar(selected)
      .then((r) => setRadar(r))
      .catch(() => setRadar({ series: [] }));
  }, [selected]);

  return (
    <div className="container">
      <header>
        <h1>NBA Career Analytics</h1>
        <div className="toolbar">
          <label>
            Player:
            <PlayerSelector players={filteredPlayers} value={selected} onChange={setSelected} />
          </label>
          <label>
            Season:
            <select
              value={seasonFilter === "all" ? "all" : String(seasonFilter)}
              onChange={(e) => {
                const v = e.target.value;
                setSeasonFilter(v === "all" ? "all" : Number(v));
              }}
            >
              <option value="all">All</option>
              {seasonOptions.map((s) => (
                <option key={s} value={String(s)}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          {loading && <span className="pill">Loading…</span>}
          {error && <span className="pill error">Error: {error}</span>}
        </div>
      </header>

      <ProfileCard player={selectedPlayer} />
      <LabelCard label={label} />

      <section className="card">
        <h3>Trajectory</h3>
        <div className="table">
          <div className="row header">
            <span>Season</span><span>Age</span><span>GP</span><span>MPG</span>
            <span>PTS/G</span><span>AST/G</span><span>REB/G</span><span>3PM/G</span>
            <span>FG%</span><span>FT%</span><span>STL/G</span><span>BLK/G</span><span>TOV/G</span><span>TS%</span>
          </div>
          {trajectory.map((t) => (
            <div className="row" key={t.season}>
              <span>{t.season}</span>
              <span>{t.age ?? "—"}</span>
              <span>{t.gp ?? "—"}</span>
              <span>{t.mpg?.toFixed(1) ?? "—"}</span>
              <span>{t.pts_per_game?.toFixed(1) ?? "—"}</span>
              <span>{t.ast_per_game?.toFixed(1) ?? "—"}</span>
              <span>{t.reb_per_game?.toFixed(1) ?? "—"}</span>
              <span>{t.fg3_per_game?.toFixed(1) ?? "—"}</span>
              <span>{formatPct(t.fg_pct)}</span>
              <span>{formatPct(t.ft_pct)}</span>
              <span>{t.stl_per_game?.toFixed(1) ?? "—"}</span>
              <span>{t.blk_per_game?.toFixed(1) ?? "—"}</span>
              <span>{t.tov_per_game?.toFixed(1) ?? "—"}</span>
              <span>{formatPct(t.ts_pct)}</span>
            </div>
          ))}
        </div>
      </section>

      <CareerChart trajectory={trajectory} />
      <SimilarList comps={comps} />
      <RadarChart data={radar} />
      {has2024Season && <ProjectionTable projection={projection} />}
    </div>
  );
}
