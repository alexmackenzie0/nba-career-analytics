type Point = {
  season: number;
  success: number | null;
};

type Props = { trajectory: { season: number; value_score?: number | null; annotation?: string | null }[] };

// Simple SVG line chart using the composite value_score as the seasonal success metric.
export default function CareerChart({ trajectory }: Props) {
  const points: Point[] = trajectory
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

  const seasons = points.map((p) => p.season);
  const successes = points.map((p) => p.success as number);
  const minS = Math.min(...successes);
  const maxS = Math.max(...successes);
  const padY = (maxS - minS) * 0.1 || 1;

  const width = 640;
  const height = 240;
  const xScale = (s: number) =>
    ((s - seasons[0]) / (seasons[seasons.length - 1] - seasons[0] || 1)) * (width - 40) + 20;
  const yScale = (v: number) => {
    const min = minS - padY;
    const max = maxS + padY;
    return height - 20 - ((v - min) / (max - min || 1)) * (height - 40);
  };

  const coords = points.map((p) => [xScale(p.season), yScale(p.success as number)]);

  const buildSmoothPath = (pts: number[][]) => {
    if (pts.length < 2) return "";
    const segs = [];
    segs.push(`M ${pts[0][0]} ${pts[0][1]}`);
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i];
      const [x1, y1] = pts[i + 1];
      const cx = (x0 + x1) / 2;
      const cy = (y0 + y1) / 2;
      // Two quadratic curves to form a smooth spline segment
      segs.push(`Q ${x0} ${y0} ${cx} ${cy}`);
      segs.push(`T ${x1} ${y1}`);
    }
    return segs.join(" ");
  };

  const path = buildSmoothPath(coords);

  return (
    <section className="card">
      <h3>Chart</h3>
      <p className="muted small">Seasonal success metric: composite value score (impact + availability + load).</p>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="260">
        <path d={path} fill="none" stroke="#2563eb" strokeWidth={3.2} strokeLinecap="round" />
        {trajectory
          .filter((t) => t.value_score !== null && t.value_score !== undefined)
          .map((t) => {
            const x = xScale(t.season);
            const y = yScale(t.value_score as number);
            return (
              <g key={t.season}>
                <circle cx={x} cy={y} r={5} fill="#1d4ed8" stroke="#0f172a" strokeWidth={1} />
                <text x={x} y={y - 8} fontSize="10" textAnchor="middle" fill="#f8fafc">
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
                <text x={x} y={height - 6} fontSize="10" textAnchor="middle" fill="#475569">
                  {t.season}
                </text>
              </g>
            );
          })}
        {/* axes */}
        <line x1={20} y1={height - 20} x2={width - 20} y2={height - 20} stroke="#cbd5e1" />
        <line x1={20} y1={20} x2={20} y2={height - 20} stroke="#cbd5e1" />
        <text x={width - 24} y={height - 24} fontSize="10" fill="#475569">
          Season
        </text>
        <text x={8} y={height / 2} fontSize="10" fill="#475569" transform={`rotate(-90 8 ${height / 2})`}>
          Success Metric
        </text>
      </svg>
    </section>
  );
}
