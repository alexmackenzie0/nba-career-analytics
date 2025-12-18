type Series = {
  player_id: number;
  name: string;
  efficiency: number;
  threes: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  distance?: number | null;
};

type Props = {
  data: { series: Series[] };
  errorMessage?: string | null;
};

const axes = [
  { key: "efficiency", label: "EFF" },
  { key: "threes", label: "3PT" },
  { key: "points", label: "PTS" },
  { key: "rebounds", label: "REB" },
  { key: "assists", label: "AST" },
  { key: "steals", label: "STL" },
  { key: "blocks", label: "BLK" },
  { key: "turnovers", label: "TOV" },
] as const;

export default function CountingGeometrySpider({ data, errorMessage = null }: Props) {
  const series = data?.series ?? [];
  if (series.length === 0) {
    return (
      <section className="card">
        <h3>Counting Stat Geometry</h3>
        {errorMessage ? (
          <p className="pill error">Error: {errorMessage}</p>
        ) : (
          <p className="muted small">No counting-geometry data available.</p>
        )}
      </section>
    );
  }

  const size = 380;
  const center = size / 2;
  const radius = size / 2 - 34;
  const rings = [0.2, 0.4, 0.6, 0.8, 1];

  const seriesColor = (idx: number) => {
    if (idx === 0) return "#38bdf8"; // selected
    const palette = ["#f97316", "#a855f7", "#22c55e", "#f59e0b", "#fb7185", "#60a5fa"];
    return palette[(idx - 1) % palette.length];
  };

  const buildPath = (s: Series) => {
    const coords = axes.map((axis, idx) => {
      const v = Math.max(0, Math.min(1, Number(s[axis.key]) || 0));
      const angle = (Math.PI * 2 * idx) / axes.length - Math.PI / 2;
      const x = center + Math.cos(angle) * radius * v;
      const y = center + Math.sin(angle) * radius * v;
      return [x, y];
    });
    return coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c[0]} ${c[1]}`).join(" ") + " Z";
  };

  return (
    <section className="card">
      <h3>Counting Stat Geometry</h3>
      <p className="muted small">
        8-axis profile built from efficiency + counting stats (normalized from similarity z-space).
      </p>
      <svg viewBox={`0 0 ${size} ${size}`} width="100%" height={size + 10}>
        {rings.map((r, idx) => (
          <polygon
            key={idx}
            points={axes
              .map((_, i) => {
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
          const lx = center + Math.cos(angle) * (radius + 16);
          const ly = center + Math.sin(angle) * (radius + 16);
          return (
            <g key={axis.key}>
              <line x1={center} y1={center} x2={x} y2={y} stroke="rgba(255,255,255,0.14)" strokeWidth={1} />
              <text x={lx} y={ly} fontSize="12" fill="rgba(248,250,252,0.92)" textAnchor="middle" dominantBaseline="middle">
                {axis.label}
              </text>
            </g>
          );
        })}

        {series.map((s, idx) => {
          const color = seriesColor(idx);
          const isSelected = idx === 0;
          return (
            <g key={s.player_id}>
              <path
                d={buildPath(s)}
                fill={isSelected ? "rgba(56,189,248,0.16)" : `${color}1a`}
                stroke={color}
                strokeWidth={isSelected ? 2.8 : 2.2}
              />
            </g>
          );
        })}
      </svg>

      <LegendTree series={series} seriesColor={seriesColor} />
    </section>
  );
}

function LegendTree({
  series,
  seriesColor,
}: {
  series: Series[];
  seriesColor: (idx: number) => string;
}) {
  const selected = series[0];
  const comps = series.slice(1, 4);
  if (!selected) return null;

  const fallback =
    "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjYwIiBoZWlnaHQ9IjE5MCIgdmlld0JveD0iMCAwIDI2MCAxOTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjI2MCIgaGVpZ2h0PSIxOTAiIHJ4PSIxNCIgZmlsbD0iI2VjZWYyZiIvPjxjaXJjbGUgY3g9IjEzMCIgY3k9Ijc2IiByPSI0OCIgZmlsbD0iI2Q5ZGRlMyIvPjxyZWN0IHg9IjYwIiB5PSIxMjQiIHdpZHRoPSIxNDAiIGhlaWdodD0iNjYiIHJ4PSIyMCIgZmlsbD0iI2Q5ZGRlMyIvPjwvc3ZnPg==";

  const hexToRgba = (hex: string, alpha: number) => {
    const m = /^#?([a-fA-F0-9]{6})$/.exec(hex);
    if (!m) return `rgba(255,255,255,${alpha})`;
    const int = parseInt(m[1], 16);
    const r = (int >> 16) & 255;
    const g = (int >> 8) & 255;
    const b = int & 255;
    return `rgba(${r},${g},${b},${alpha})`;
  };

  const renderHeadshot = (playerId: number, name: string, className: string) => {
    const primary = `https://cdn.nba.com/headshots/nba/latest/260x190/${playerId}.png`;
    const alternate = `https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/${playerId}.png`;
    return (
      <img
        className={className}
        src={primary}
        alt={name}
        referrerPolicy="no-referrer"
        data-stage="primary"
        onError={(e) => {
          const img = e.currentTarget;
          const stage = img.dataset.stage;
          if (stage === "primary") {
            img.src = alternate;
            img.dataset.stage = "alternate";
          } else {
            img.src = fallback;
            img.dataset.stage = "fallback";
          }
        }}
      />
    );
  };

  return (
    <div className="spider-legend-tree">
      <div className="spider-legend-top">
        <div className="legend-node legend-node-selected">
          {renderHeadshot(selected.player_id, selected.name, "spider-headshot spider-headshot-xl")}
          <div className="legend-node-text">
            <div className="legend-node-title">Selected</div>
            <div className="legend-node-name">{selected.name}</div>
          </div>
        </div>
      </div>

      <div className="spider-legend-bottom">
        {comps.map((c, idx) => {
          const color = seriesColor(idx + 1);
          return (
            <div
              className="legend-node legend-node-comp"
              key={c.player_id}
              style={{ borderColor: hexToRgba(color, 0.45) }}
            >
              <div className="legend-rank">#{idx + 1}</div>
              {renderHeadshot(c.player_id, c.name, "spider-headshot spider-headshot-lg")}
              <div className="legend-node-text">
                <div className="legend-node-name">{c.name}</div>
                {c.distance != null && <div className="muted small">dist {Number(c.distance).toFixed(2)}</div>}
              </div>
              <span className="spider-swatch spider-swatch-lg" style={{ background: color }} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
