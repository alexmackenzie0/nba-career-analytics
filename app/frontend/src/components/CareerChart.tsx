type Point = {
  season: number;
  success: number | null;
};

type Props = {
  title?: string;
  showSubtitle?: boolean;
  svgHeight?: number | string;
  trajectory: { season: number; value_score?: number | null; annotation?: string | null }[];
  comparisonTrajectory?: { season: number; value_score?: number | null }[];
  comparisonName?: string | null;
};

// Simple SVG line chart using the composite value_score as the seasonal success metric.
export default function CareerChart({
  title = "Chart",
  showSubtitle = true,
  svgHeight = 260,
  trajectory,
  comparisonTrajectory = [],
  comparisonName = null,
}: Props) {
  const points: Point[] = trajectory
    .filter((t) => t.value_score !== null && t.value_score !== undefined)
    .map((t) => ({ season: t.season, success: t.value_score ?? null }));

  const compPoints: Point[] = comparisonTrajectory
    .filter((t) => t.value_score !== null && t.value_score !== undefined)
    .map((t) => ({ season: t.season, success: t.value_score ?? null }));

  if (points.length === 0) {
    return (
      <section className="card">
        <h3>Chart</h3>
        <p>No data available.</p>
      </section>
    );
  }

  const allSeasons = [...points.map((p) => p.season), ...compPoints.map((p) => p.season)];
  const minSeason = Math.min(...allSeasons);
  const maxSeason = Math.max(...allSeasons);

  const successes = [...points.map((p) => p.success as number), ...compPoints.map((p) => p.success as number)];
  const minS = Math.min(...successes);
  const maxS = Math.max(...successes);
  const padY = (maxS - minS) * 0.1 || 1;

  const width = 640;
  // Slightly taller viewBox + larger bottom padding prevents axis labels from being clipped
  // when the chart is constrained into a short dashboard footer.
  const height = 270;
  const pad = { left: 24, right: 22, top: 22, bottom: 40 };

  const xScale = (s: number) =>
    ((s - minSeason) / (maxSeason - minSeason || 1)) * (width - pad.left - pad.right) + pad.left;
  const yScale = (v: number) => {
    const min = minS - padY;
    const max = maxS + padY;
    return (
      height -
      pad.bottom -
      ((v - min) / (max - min || 1)) * (height - pad.top - pad.bottom)
    );
  };

  const coords = points.map((p) => [xScale(p.season), yScale(p.success as number)]);
  const compCoords = compPoints.map((p) => [xScale(p.season), yScale(p.success as number)]);

  const buildSmoothPath = (pts: number[][]) => {
    if (pts.length < 2) return "";
    const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
    const tension = 0.9;

    const p = (i: number) => pts[clamp(i, 0, pts.length - 1)];
    let d = `M ${pts[0][0]} ${pts[0][1]}`;

    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = p(i - 1);
      const [x1, y1] = p(i);
      const [x2, y2] = p(i + 1);
      const [x3, y3] = p(i + 2);

      // Catmull-Rom to cubic Bezier
      const c1x = x1 + ((x2 - x0) / 6) * tension;
      const c1y = y1 + ((y2 - y0) / 6) * tension;
      const c2x = x2 - ((x3 - x1) / 6) * tension;
      const c2y = y2 - ((y3 - y1) / 6) * tension;

      d += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`;
    }

    return d;
  };

  const path = buildSmoothPath(coords);
  const compPath = buildSmoothPath(compCoords);

  const buildTicks = () => {
    const span = maxSeason - minSeason;
    const desired = 8;
    const step = Math.max(1, Math.ceil(span / desired));
    const ticks = [];
    for (let y = minSeason; y <= maxSeason; y += step) ticks.push(y);
    if (ticks[ticks.length - 1] !== maxSeason) ticks.push(maxSeason);
    return ticks;
  };
  const ticks = buildTicks();

  return (
    <section className="card">
      <h3>{title}</h3>
      {showSubtitle && (
        <p className="muted small">Seasonal success metric: composite value score (impact + availability + load).</p>
      )}
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={svgHeight}>
        <defs>
          <linearGradient id="successLine" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#f97316" />
            <stop offset="55%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#2563eb" />
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#38bdf8" floodOpacity="0.35" />
            <feDropShadow dx="0" dy="0" stdDeviation="6" floodColor="#2563eb" floodOpacity="0.22" />
          </filter>
        </defs>

        {compPath && (
          <path
            d={compPath}
            fill="none"
            stroke="rgba(248,250,252,0.92)"
            strokeWidth={2.6}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.85}
          />
        )}

        {/* Comparison points (no value labels, no annotations) */}
        {compPoints.map((p) => (
          <g key={`comp-${p.season}`}>
            <circle cx={xScale(p.season)} cy={yScale(p.success as number)} r={4.5} fill="rgba(248,250,252,0.92)" opacity={0.9} />
          </g>
        ))}

        <path
          d={path}
          fill="none"
          stroke="url(#successLine)"
          strokeWidth={3.6}
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#glow)"
        />
        {trajectory
          .filter((t) => t.value_score !== null && t.value_score !== undefined)
          .map((t) => {
            const x = xScale(t.season);
            const y = yScale(t.value_score as number);
            return (
              <g key={t.season}>
                <circle cx={x} cy={y} r={6} fill="#38bdf8" opacity={0.9} />
                <circle cx={x} cy={y} r={9} fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth={2} />
                <text x={x} y={y - 10} fontSize="10" textAnchor="middle" fill="rgba(248,250,252,0.75)">
                  {(t.value_score as number)?.toFixed(1)}
                </text>
                {t.annotation && (
                  (() => {
                    const yAbove = y - 60;
                    const yBelow = y + 40;
                    const useBelow = yAbove < 10; // too close to top edge
                    const yPos = useBelow ? yBelow : yAbove;
                    const rotationCenterY = yPos;
                    return (
                      <text
                        x={x}
                        y={yPos}
                        fontSize="10"
                        textAnchor="middle"
                        fill="#ef4444"
                        transform={`rotate(-90 ${x} ${rotationCenterY})`}
                      >
                        {t.annotation}
                      </text>
                    );
                  })()
                )}
              </g>
            );
          })}

        {/* Legend */}
        {compPoints.length > 0 && (
          <g>
            <rect
              x={width - 250}
              y={8}
              width={224}
              height={34}
              rx={10}
              fill="rgba(0,0,0,0.35)"
              stroke="rgba(255,255,255,0.10)"
            />
            <circle cx={width - 234} cy={25} r={5} fill="#38bdf8" />
            <text x={width - 222} y={29} fontSize="11" fill="rgba(248,250,252,0.9)">
              Selected
            </text>
            <line
              x1={width - 166}
              y1={25}
              x2={width - 144}
              y2={25}
              stroke="rgba(248,250,252,0.92)"
              strokeWidth={2.6}
              strokeLinecap="round"
            />
            <text x={width - 136} y={29} fontSize="11" fill="rgba(248,250,252,0.85)">
              {comparisonName ? `Comp: ${comparisonName}` : "Top comp"}
            </text>
          </g>
        )}

        {/* axes */}
        <line
          x1={pad.left}
          y1={height - pad.bottom}
          x2={width - pad.right}
          y2={height - pad.bottom}
          stroke="rgba(226,232,240,0.35)"
        />
        <line
          x1={pad.left}
          y1={pad.top}
          x2={pad.left}
          y2={height - pad.bottom}
          stroke="rgba(226,232,240,0.35)"
        />
        {ticks.map((yr) => {
          const x = xScale(yr);
          return (
            <g key={yr}>
              <line
                x1={x}
                y1={height - pad.bottom}
                x2={x}
                y2={height - pad.bottom + 4}
                stroke="rgba(226,232,240,0.35)"
              />
              <text
                x={x}
                y={height - pad.bottom + 18}
                fontSize="10"
                textAnchor="middle"
                fill="rgba(147,164,193,0.9)"
              >
                {yr}
              </text>
            </g>
          );
        })}
        <text
          x={10}
          y={height / 2}
          fontSize="10"
          fill="rgba(147,164,193,0.9)"
          transform={`rotate(-90 10 ${height / 2})`}
        >
          Success Metric
        </text>
      </svg>
    </section>
  );
}
