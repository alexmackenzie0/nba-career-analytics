type Props = {
  comps: { player_id: number; name: string; distance: number; similarity_rank: number }[];
};

export default function SimilarList({ comps }: Props) {
  return (
    <section className="card">
      <h3>Similar Players</h3>
      {comps.length === 0 ? (
        <p>No comps yet.</p>
      ) : (
        <ul className="list">
          {comps.map((c) => (
            <li key={c.player_id}>
              <strong>#{c.similarity_rank}</strong> {c.name} <span className="muted">(dist {c.distance.toFixed(2)})</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
