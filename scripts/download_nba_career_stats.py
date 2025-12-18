"""
download_nba_career_stats.py

Slow + safe downloader:
- Only players with FROM_YEAR >= 2000
- Only seasons with SEASON_START_YEAR >= 2000
- Appends each successful player's rows to:
    data/raw/career_stats_2000_onward.csv
- Resumes automatically by skipping already-saved PLAYER_IDs
"""

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict

import pandas as pd
from nba_api.stats.endpoints import commonallplayers, playercareerstats

# ---------------- CONFIG ---------------- #
MIN_SEASON_YEAR = 2000
FROM_YEAR_FILTER = 2000
MAX_WORKERS = 4          # very conservative: only 2 threads
MAX_RETRIES = 3
SLEEP_AFTER_SUCCESS = 0.6  # sleep after each successful player
RETRY_SLEEP = 2.4        # sleep between retries on failure
OUTPUT_FILE = Path("data/raw/career_stats_2000_onward.csv")
# ---------------------------------------- #


def get_players_since_2000() -> pd.DataFrame:
    """Fetch full player list and filter to FROM_YEAR >= 2000."""
    print("Fetching full NBA player list...")
    players_df = commonallplayers.CommonAllPlayers(
        is_only_current_season=0,
        league_id="00"
    ).get_data_frames()[0]

    players_df["FROM_YEAR"] = pd.to_numeric(players_df["FROM_YEAR"], errors="coerce")
    filtered = players_df[players_df["FROM_YEAR"] >= FROM_YEAR_FILTER].copy()
    filtered = filtered.reset_index(drop=True)

    print(f"Total players: {len(players_df)} | Players since 2000: {len(filtered)}")
    return filtered


def load_existing_players() -> set:
    """Return a set of PLAYER_IDs already stored in the output CSV."""
    if not OUTPUT_FILE.exists():
        return set()

    try:
        df = pd.read_csv(OUTPUT_FILE, usecols=["PLAYER_ID"])
        existing_ids = set(df["PLAYER_ID"].unique())
        print(f"Found {len(existing_ids)} players already in {OUTPUT_FILE}.")
        return existing_ids
    except Exception as e:
        print(f"Warning: could not read existing file ({e}). Starting fresh.")
        return set()


def append_to_csv(df: pd.DataFrame):
    """Append a chunk of rows to the master CSV file."""
    header = not OUTPUT_FILE.exists()  # write header only if file is new
    df.to_csv(OUTPUT_FILE, mode="a", header=header, index=False)


def fetch_single_player(info: Dict, already_done: set) -> Optional[pd.DataFrame]:
    player_id = info["player_id"]
    player_name = info["player_name"]
    pos = info["pos"]
    total = info["total"]

    if player_id in already_done:
        print(f"[{pos}/{total}] Skipping {player_name} ({player_id}) — already saved.")
        return None

    print(f"[{pos}/{total}] Fetching {player_name} ({player_id})...")

    retries = 0
    df = pd.DataFrame()

    while retries < MAX_RETRIES:
        try:
            career = playercareerstats.PlayerCareerStats(
                player_id=player_id,
                timeout=60,
            )
            df = career.get_data_frames()[0]
            break
        except Exception as e:
            retries += 1
            print(f"  -> Retry {retries}/{MAX_RETRIES} failed for {player_name}: {e}")
            if retries >= MAX_RETRIES:
                print(f"  -> FAILED for {player_name}. Skipping.")
                return None
            time.sleep(RETRY_SLEEP)

    if df.empty:
        print(f"  -> No stats for {player_name}.")
        return None

    # Filter to seasons >= MIN_SEASON_YEAR
    df["SEASON_START_YEAR"] = df["SEASON_ID"].str.slice(0, 4).astype(int)
    df = df[df["SEASON_START_YEAR"] >= MIN_SEASON_YEAR].copy()

    if df.empty:
        print(f"  -> All seasons < {MIN_SEASON_YEAR} for {player_name}.")
        return None

    df["PLAYER_ID"] = player_id
    df["PLAYER_NAME"] = player_name

    time.sleep(SLEEP_AFTER_SUCCESS)
    return df


def fetch_player_seasons_multithread(players_df: pd.DataFrame):
    existing = load_existing_players()

    print(
        f"\nStarting download for {len(players_df)} players "
        f"(FROM_YEAR >= {FROM_YEAR_FILTER})..."
    )
    print(f"Max workers: {MAX_WORKERS}")
    print(f"Output file: {OUTPUT_FILE}\n")

    jobs = []
    total = len(players_df)

    # ✅ Resume point: next player after Marcelo Huertas ([907/2188])
    START_FROM_INDEX = 2064  # 1-based position

    for idx, row in players_df.iterrows():
        # Skip players before the resume point
        if START_FROM_INDEX is not None and (idx + 1) < START_FROM_INDEX:
            continue

        jobs.append({
            "pos": idx + 1,
            "total": total,
            "player_id": row["PERSON_ID"],
            "player_name": row["DISPLAY_FIRST_LAST"],
        })

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_single_player, job, existing): job for job in jobs}

        for future in as_completed(futures):
            df_chunk = future.result()
            if df_chunk is not None and not df_chunk.empty:
                append_to_csv(df_chunk)


def main():
    Path("data/raw").mkdir(parents=True, exist_ok=True)

    players_df = get_players_since_2000()
    fetch_player_seasons_multithread(players_df)

    print("\n==============================================")
    print(" COMPLETE — all available players processed. ")
    print(f" Data stored incrementally at:\n {OUTPUT_FILE}")
    print("==============================================\n")


if __name__ == "__main__":
    main()
