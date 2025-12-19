# Utility to fetch bio info (height/weight/position) for players in a raw
# players CSV.
#
# IMPORTANT: restart-safe workflow
# - Appends each successful fetch to OUT_DYNAMIC_CSV immediately (so timeouts
#   or interruptions don't wipe progress).
# - At the end, merges OUT_DYNAMIC_CSV into OUT_PERMANENT_CSV (deduped by
#   player_id). You can later merge OUT_PERMANENT_CSV into parquet separately.
#
# Set the absolute paths below before running.

from pathlib import Path
import time
import pandas as pd
from nba_api.stats.endpoints import commonplayerinfo


# Set these to full paths before running
PLAYERS_CSV = "/Users/alexmackenzie/projects/nba-career-analytics/data/raw/players_2000_onward.csv"
# Per-run dynamic progress file (append-only)
OUT_DYNAMIC_CSV = "/Users/alexmackenzie/projects/nba-career-analytics/data/clean/player_bio.dynamic.csv"
# Permanent cumulative output (deduped by player_id)
OUT_PERMANENT_CSV = "/Users/alexmackenzie/projects/nba-career-analytics/data/clean/player_bio.csv"
# Set the 1-based index to resume from (e.g., 603 means skip first 602 players).
START_FROM_INDEX = 1200
# Skip player_ids already present in OUT_PERMANENT_CSV and OUT_DYNAMIC_CSV.
SKIP_EXISTING = True
# Pause between requests (seconds) to reduce rate-limit/timeouts.
PAUSE_SECONDS = 0.3


def load_player_ids(path: str) -> pd.Series:
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    return df["person_id"].dropna().astype(int).unique()

def load_existing_ids(path: str) -> set[int]:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        return set()
    if df.empty or "player_id" not in df.columns:
        return set()
    return set(df["player_id"].dropna().astype(int).tolist())


def fetch_player(pid: int, pause: float) -> dict:
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
    # Ensure output dirs exist
    Path(OUT_DYNAMIC_CSV).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_PERMANENT_CSV).parent.mkdir(parents=True, exist_ok=True)

    all_ids = list(load_player_ids(PLAYERS_CSV))
    original_total = len(all_ids)
    start_offset = max(START_FROM_INDEX - 1, 0)
    ids = all_ids[start_offset:] if start_offset else all_ids

    existing = set()
    if SKIP_EXISTING:
        existing |= load_existing_ids(OUT_PERMANENT_CSV)
        existing |= load_existing_ids(OUT_DYNAMIC_CSV)

    wrote_dynamic = 0
    for idx, pid in enumerate(ids, START_FROM_INDEX):
        pid_int = int(pid)
        if SKIP_EXISTING and pid_int in existing:
            print(f"[{idx}/{original_total}] player_id={pid_int} SKIP (already saved)")
            continue
        try:
            info = fetch_player(pid_int, pause=PAUSE_SECONDS)
            # Append row immediately so we don't lose progress if interrupted.
            pd.DataFrame([info]).to_csv(
                OUT_DYNAMIC_CSV,
                mode="a",
                header=not Path(OUT_DYNAMIC_CSV).exists(),
                index=False,
            )
            existing.add(pid_int)
            wrote_dynamic += 1
            print(f"[{idx}/{original_total}] {info['name']} pos={info['position']} height={info['height']} weight={info['weight']}")
        except Exception as e:
            print(f"[{idx}/{original_total}] player_id={pid_int} FAILED: {e}")

    # Merge dynamic into permanent (dedupe by player_id).
    try:
        dyn_df = pd.read_csv(OUT_DYNAMIC_CSV)
    except FileNotFoundError:
        dyn_df = pd.DataFrame()
    try:
        perm_df = pd.read_csv(OUT_PERMANENT_CSV)
    except FileNotFoundError:
        perm_df = pd.DataFrame()

    if dyn_df.empty:
        print("No rows in dynamic file to merge.")
        print(f"Run complete. Appended {wrote_dynamic} new rows to {OUT_DYNAMIC_CSV}")
        return

    merged = pd.concat([perm_df, dyn_df], ignore_index=True)
    if "player_id" in merged.columns:
        merged["player_id"] = merged["player_id"].astype(int)
        merged = merged.drop_duplicates(subset=["player_id"], keep="last")
    merged.to_csv(OUT_PERMANENT_CSV, index=False)

    print(f"Merged -> {OUT_PERMANENT_CSV} ({len(merged)} unique players)")
    print(f"Run complete. Appended {wrote_dynamic} new rows to {OUT_DYNAMIC_CSV}")


if __name__ == "__main__":
    main()
