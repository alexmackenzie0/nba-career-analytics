type Props = { projection: any[] };

export default function ProjectionTable({ projection }: Props) {
  return (
    <section className="card">
      <h3>Projection</h3>
      <div className="table">
        <div className="row header">
          <span>Season</span><span>Age</span><span>GP</span><span>MPG</span>
          <span>PTS/G</span><span>AST/G</span><span>REB/G</span><span>3PM/G</span>
          <span>FG%</span><span>FT%</span><span>STL/G</span><span>BLK/G</span><span>TOV/G</span><span>TS%</span>
        </div>
        {projection.map((p) => (
          <div className="row" key={p.season}>
            <span>{p.season}</span>
            <span>{p.age !== null && p.age !== undefined ? Math.round(p.age) : "—"}</span>
            <span>{p.gp_pred !== null && p.gp_pred !== undefined ? Math.round(p.gp_pred) : "—"}</span>
            <span>{p.mpg_pred?.toFixed(1) ?? "—"}</span>
            <span>{p.pts_per_game_pred?.toFixed(1) ?? "—"}</span>
            <span>{p.ast_per_game_pred?.toFixed(1) ?? "—"}</span>
            <span>{p.reb_per_game_pred?.toFixed(1) ?? "—"}</span>
            <span>{p.fg3_per_game_pred?.toFixed(1) ?? "—"}</span>
            <span>{p.fg_pct_pred !== undefined && p.fg_pct_pred !== null ? (p.fg_pct_pred * 100).toFixed(1) + "%" : "—"}</span>
            <span>{p.ft_pct_pred !== undefined && p.ft_pct_pred !== null ? (p.ft_pct_pred * 100).toFixed(1) + "%" : "—"}</span>
            <span>{p.stl_per_game_pred?.toFixed(2) ?? "—"}</span>
            <span>{p.blk_per_game_pred?.toFixed(2) ?? "—"}</span>
            <span>{p.tov_per_game_pred?.toFixed(2) ?? "—"}</span>
            <span>{p.ts_pct_pred !== undefined && p.ts_pct_pred !== null ? (p.ts_pct_pred * 100).toFixed(1) + "%" : "—"}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
