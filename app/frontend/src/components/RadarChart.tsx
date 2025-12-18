type Series = {
  player_id: number;
  name: string;
  pts_per_game: number | null;
  ast_per_game: number | null;
  reb_per_game: number | null;
  fg3_per_game: number | null;
  ts_pct: number | null;
  availability: number | null;
  value_score: number | null;
};

type Props = {
  data: { series: Series[] };
};

const axes = [
  { key: "pts_per_game", label: "PTS" },
  { key: "ast_per_game", label: "AST" },
  { key: "reb_per_game", label: "REB" },
  { key: "fg3_per_game", label: "3PM" },
  { key: "ts_pct", label: "TS%" },
  { key: "availability", label: "AVAIL" },
  { key: "value_score", label: "VALUE" },
] as const;

export default function RadarChart({ data }: Props) {
  if (!data?.series || data.series.length === 0) return null;

  const size = 360;
  const center = size / 2;
  const radius = size / 2 - 30;

  // Normalize values per axis across all series
  const maxPerAxis: Record<string, number> = {};
  axes.forEach((a) => {
    const vals = data.series
      .map((s) => s[a.key])
      .filter((v) => v !== null && v !== undefined) as number[];
    const maxVal = vals.length ? Math.max(...vals) : 1;
    maxPerAxis[a.key] = maxVal || 1;
  });

  const colors = ["#f97316", "#38bdf8", "#a855f7", "#22c55e", "#f59e0b"];

  const buildPath = (series: Series) => {
    const coords = axes.map((axis, idx) => {
      const raw = series[axis.key] ?? 0;
      const max = maxPerAxis[axis.key] || 1;
      const val = Math.min(raw / max, 1);
      const angle = (Math.PI * 2 * idx) / axes.length - Math.PI / 2;
      const x = center + Math.cos(angle) * radius * val;
      const y = center + Math.sin(angle) * radius * val;
      return [x, y];
    });
    return coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c[0]} ${c[1]}`).join(" ") + " Z";
  };

  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <section className="card">
      <h3>Similarity Radar</h3>
      <p className="muted small">Latest-season profile vs comps (normalized per axis).</p>
      <svg viewBox={`0 0 ${size} ${size}`} width="100%" height={size + 20}>
        {rings.map((r, idx) => (
          <polygon
            key={idx}
            points={axes
              .map((axis, i) => {
                const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
                const x = center + Math.cos(angle) * radius * r;
                const y = center + Math.sin(angle) * radius * r;
                return `${x},${y}`;
              })
              .join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={1}
          />
        ))}
        {axes.map((axis, i) => {
          const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
          const x = center + Math.cos(angle) * radius;
          const y = center + Math.sin(angle) * radius;
          const lx = center + Math.cos(angle) * (radius + 12);
          const ly = center + Math.sin(angle) * (radius + 12);
          return (
            <g key={axis.key}>
              <line x1={center} y1={center} x2={x} y2={y} stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
              <text x={lx} y={ly} fontSize="11" fill="#e2e8f0" textAnchor="middle" dominantBaseline="middle">
                {axis.label}
              </text>
            </g>
          );
        })}

        {data.series.map((s, idx) => {
          const color = colors[idx % colors.length];
          const path = buildPath(s);
          return (
            <g key={s.player_id}>
              <path d={path} fill={color + "33"} stroke={color} strokeWidth={2} />
              {axes.map((axis, i) => {
                const raw = s[axis.key] ?? 0;
                const max = maxPerAxis[axis.key] || 1;
                const val = Math.min(raw / max, 1);
                const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
                const x = center + Math.cos(angle) * radius * val;
                const y = center + Math.sin(angle) * radius * val;
                return <circle key={axis.key} cx={x} cy={y} r={3} fill={color} />;
              })}
              <text x={center} y={size - 6 - idx * 14} fontSize="11" fill={color} textAnchor="middle">
                {s.name}
              </text>
            </g>
          );
        })}
      </svg>
    </section>
  );
}
