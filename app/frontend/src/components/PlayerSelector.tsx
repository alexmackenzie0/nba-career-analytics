import { useState } from "react";

type Props = {
  players: any[];
  value: number | null;
  onChange: (id: number) => void;
};

export default function PlayerSelector({ players, value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const maxUiSeason = 2024;
  const filtered = players
    .filter((p) => p.player_id && p.player_id !== "" && p.player_id !== null)
    .filter((p) => p.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="player-selector">
      <div className="player-selector-row">
        <input
          type="text"
          placeholder="Search player…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="player-search"
        />
        <select value={value ?? ""} onChange={(e) => onChange(Number(e.target.value))}>
          {filtered.map((p) => (
            <option key={p.player_id} value={p.player_id}>
              {p.name} ({p.from_year ?? "—"}-
              {p.to_year == null ? "—" : Math.min(Number(p.to_year), maxUiSeason)})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
