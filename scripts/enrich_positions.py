"""
Enrich player positions and save to data/clean/player_positions.parquet.
Uses commonplayerinfo for every player_id (static players listing does not include position).
Run once with network enabled; respects a small pause to avoid rate limits.
"""
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.library.parameters import LeagueID


def fetch_position_api(player_id: int, pause: float = 0.6) -> str | None:
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, league_id=LeagueID.nba).get_data_frames()[0]
        pos = info.get("POSITION")
        # small pause to be gentle with the API
        time.sleep(pause)
        return pos if pd.notna(pos) else None
    except Exception as e:
        print(f"  error fetching player_id={player_id}: {e}")
        time.sleep(pause)
        return None


def main():
    root = Path(__file__).resolve().parents[1]
    parquet_path = root / "data/clean/player_seasons.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing {parquet_path}, run prepare_player_seasons.py first.")

    df = pd.read_parquet(parquet_path)
    player_ids = sorted(df["player_id"].unique())

    out = []
    fetched_api = 0
    for idx, pid in enumerate(player_ids, 1):
        pid_int = int(pid)
        pos = fetch_position_api(pid_int)
        if pos:
            fetched_api += 1
        out.append({"player_id": pid_int, "primary_position": pos})
        print(f"{idx}/{len(player_ids)} player_id={pid_int} position={pos}")

    out_df = pd.DataFrame(out)
    out_path = root / "data/clean/player_positions.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out_path, index=False)
    print(f"Saved positions to {out_path} ({len(out_df)} rows). Fetched via API: {fetched_api}")


if __name__ == "__main__":
    main()
