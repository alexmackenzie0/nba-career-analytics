import time
from pathlib import Path

import pandas as pd
import requests  # NEW

print("Script started...")

# Directory to store raw combined data
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Range of seasons to download (customize as needed)
START_YEAR = 1980
END_YEAR = 2024  # last completed NBA season

all_seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
    print(f"Downloading season {year} from {url} ...")

    try:
        # --- Use requests to handle HTTPS + certificates ---
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raise if HTTP error

        # Pass HTML content directly to pandas
        tables = pd.read_html(response.text)
        df = tables[0]

        # Remove repeated header rows inside the table
        df = df[df["Rk"] != "Rk"]

        # Add season column
        df["season"] = year

        all_seasons.append(df)

        # Be polite: avoid rapid-fire requests
        time.sleep(2)

    except Exception as e:
        print(f"Failed to process {year}: {e}")

if not all_seasons:
    print("No data was downloaded. Exiting.")
else:
    # Combine all years
    combined = pd.concat(all_seasons, ignore_index=True)

    # Normalize column names
    combined.columns = [
        c.strip().lower().replace(" ", "_").replace("%", "pct")
        for c in combined.columns
    ]

    # Save combined file
    out_path = RAW_DIR / "bref_per_game_1980_2024.csv"
    combined.to_csv(out_path, index=False)

    print(f"\nSUCCESS: Saved combined dataset to {out_path}")
