type Props = {
  title?: string;
  comps: { player_id: number; name: string; distance: number; similarity_rank: number }[];
};

export default function SimilarList({ title = "Similar Players", comps }: Props) {
  const fallback =
    "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjYwIiBoZWlnaHQ9IjE5MCIgdmlld0JveD0iMCAwIDI2MCAxOTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjI2MCIgaGVpZ2h0PSIxOTAiIHJ4PSIxNCIgZmlsbD0iI2VjZWYyZiIvPjxjaXJjbGUgY3g9IjEzMCIgY3k9Ijc2IiByPSI0OCIgZmlsbD0iI2Q5ZGRlMyIvPjxyZWN0IHg9IjYwIiB5PSIxMjQiIHdpZHRoPSIxNDAiIGhlaWdodD0iNjYiIHJ4PSIyMCIgZmlsbD0iI2Q5ZGRlMyIvPjwvc3ZnPg==";
  const sorted = [...comps]
    .filter((c) => Number.isFinite(c.distance))
    .sort((a, b) => a.distance - b.distance);
  // Sorted by smallest distance first for readability.

  return (
    <section className="card">
      <h3>{title}</h3>
      {sorted.length === 0 ? (
        <p>No comps yet.</p>
      ) : (
        <div className="similar-grid">
          {sorted.map((c, idx) => {
            const primary = `https://cdn.nba.com/headshots/nba/latest/260x190/${c.player_id}.png`;
            const alternate = `https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/${c.player_id}.png`;
            return (
              <div className="similar-card" key={c.player_id}>
                <div className="similar-rank">#{idx + 1}</div>
                <img
                  className="similar-img"
                  src={primary}
                  alt={c.name}
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
                <div className="similar-meta">
                  <div className="similar-name">{c.name}</div>
                  <div className="muted small">distance {c.distance.toFixed(2)}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
