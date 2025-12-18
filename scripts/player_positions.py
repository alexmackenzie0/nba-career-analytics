# Utility to fetch bio info (height/weight/position) for all players in a raw
# players CSV. Writes a separate CSV so you can merge into parquet later, and
# logs progress per player. Set the absolute input/output paths below.

import time
import pandas as pd
from nba_api.stats.endpoints import commonplayerinfo


# Set these to full paths before running
PLAYERS_CSV = "/Users/alexmackenzie/projects/nba-career-analytics/data/raw/players_2000_onward.csv"
OUT_CSV = "/Users/alexmackenzie/projects/nba-career-analytics/data/clean/player_bio.csv"
# Set the 1-based index to resume from (e.g., 603 means skip first 602 players).
START_FROM_INDEX = 1805


def load_player_ids(path: str) -> pd.Series:
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    return df["person_id"].dropna().astype(int).unique()


def fetch_player(pid: int, pause: float = 0.3) -> dict:
    info = commonplayerinfo.CommonPlayerInfo(player_id=pid).get_normalized_dict()["CommonPlayerInfo"][0]
    time.sleep(pause)  # be gentle to the API
    return {
        "player_id": pid,
        "name": info.get("DISPLAY_FIRST_LAST"),
        "height": info.get("HEIGHT"),
        "weight": info.get("WEIGHT"),
        "position": info.get("POSITION"),
    }


def main():
    all_ids = list(load_player_ids(PLAYERS_CSV))
    original_total = len(all_ids)
    start_offset = max(START_FROM_INDEX - 1, 0)
    ids = all_ids[start_offset:] if start_offset else all_ids
    out = []
    remaining = len(ids)
    for idx, pid in enumerate(ids, START_FROM_INDEX):
        try:
            info = fetch_player(int(pid))
            out.append(info)
            print(f"[{idx}/{original_total}] {info['name']} pos={info['position']} height={info['height']} weight={info['weight']}")
        except Exception as e:
            print(f"[{idx}/{original_total}] player_id={pid} FAILED: {e}")

    pd.DataFrame(out).to_csv(OUT_CSV, index=False)
    print(f"Saved {len(out)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
