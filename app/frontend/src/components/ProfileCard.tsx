import { useEffect, useMemo, useState } from "react";

type Props = {
  player: any;
};

export default function ProfileCard({ player }: Props) {
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

  return (
    <section className="card profile-card">
      <div className="profile-info">
        <div>
          <h3>{player.name}</h3>
        </div>
        <img
          className="headshot"
          src={src}
          alt={player.name}
          referrerPolicy="no-referrer"
          onError={onError}
        />
      </div>
    </section>
  );
}
