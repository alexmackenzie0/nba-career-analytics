import { useEffect, useMemo, useState } from "react";

type Props = {
  player: any;
  label?: string | null;
  injuryLabel?: string | null;
};

export default function ProfileCard({ player, label = null, injuryLabel = null }: Props) {
  const maxUiSeason = 2024;
  const fallback =
    "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjYwIiBoZWlnaHQ9IjE5MCIgdmlld0JveD0iMCAwIDI2MCAxOTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjI2MCIgaGVpZ2h0PSIxOTAiIHJ4PSIxNCIgZmlsbD0iI2VjZWYyZiIvPjxjaXJjbGUgY3g9IjEzMCIgY3k9Ijc2IiByPSI0OCIgZmlsbD0iI2Q5ZGRlMyIvPjxyZWN0IHg9IjYwIiB5PSIxMjQiIHdpZHRoPSIxNDAiIGhlaWdodD0iNjYiIHJ4PSIyMCIgZmlsbD0iI2Q5ZGRlMyIvPjwvc3ZnPg==";
  const playerId = player?.player_id;
  const [src, setSrc] = useState(fallback);
  const [triedAlternate, setTriedAlternate] = useState(false);
  const [triedLegacy, setTriedLegacy] = useState(false);

  const primary = useMemo(
    () => (playerId ? `https://cdn.nba.com/headshots/nba/latest/260x190/${playerId}.png` : null),
    [playerId]
  );
  const legacy = useMemo(
    () => (playerId ? `https://cdn.nba.com/headshots/nba/latest/1040x760/${playerId}.png` : null),
    [playerId]
  );
  const alternate = useMemo(
    () => (playerId ? `https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/${playerId}.png` : null),
    [playerId]
  );

  useEffect(() => {
    // Reset the headshot source whenever the selected player changes.
    if (primary) {
      setSrc(primary);
    } else {
      setSrc(fallback);
    }
    setTriedAlternate(false);
    setTriedLegacy(false);
  }, [primary]);

  const onError = () => {
    if (!triedAlternate && alternate) {
      setSrc(alternate);
      setTriedAlternate(true);
    } else if (!triedLegacy && legacy) {
      setSrc(legacy);
      setTriedLegacy(true);
    } else if (src !== fallback) {
      setSrc(fallback);
    }
  };

  if (!player) return null;
  const position = typeof player.position === "string" ? player.position.trim() : "";
  const showPosition = position.length > 0 && /[a-zA-Z]/.test(position);
  const showLabel = typeof label === "string" && label.trim().length > 0 && label !== "—";
  const height = typeof player.height === "string" ? player.height : null;
  const weight = player.weight != null ? Number(player.weight) : null;
  const displayedSeasonCount = (() => {
    const played: unknown = player.seasons_played;
    if (Array.isArray(played)) {
      const count = played.filter((s) => typeof s === "number" && s <= maxUiSeason).length;
      return count > 0 ? count : null;
    }
    const raw = typeof player.season_count === "number" ? player.season_count : null;
    if (raw == null || Number.isNaN(raw)) return null;
    const toYear = player.to_year != null ? Number(player.to_year) : null;
    const adjusted = toYear != null && toYear > maxUiSeason ? raw - 1 : raw;
    return Math.max(0, adjusted);
  })();

  return (
    <section className="card profile-card">
      <div className="profile-hero">
        <img
          className="headshot headshot-lg"
          src={src}
          alt={player.name}
          referrerPolicy="no-referrer"
          onError={onError}
        />
        <div className="profile-meta">
          <div className="player-name">{player.name}</div>
          <div className="profile-chips">
            {showPosition && <span className="chip chip-accent">{position}</span>}
            {height && <span className="chip chip-accent">{height}</span>}
            {weight && <span className="chip chip-accent">{weight} lb</span>}
            <span className="chip">
              {player.from_year ?? "—"}-
              {player.to_year == null ? "—" : Math.min(Number(player.to_year), maxUiSeason)}
            </span>
            {displayedSeasonCount != null && (
              <span className="chip">
                {displayedSeasonCount} {displayedSeasonCount === 1 ? "season" : "seasons"}
              </span>
            )}
            {showLabel && <span className="chip chip-label">{label}</span>}
            {injuryLabel && <span className="chip chip-injury">{injuryLabel}</span>}
          </div>
        </div>
      </div>
    </section>
  );
}
