import pandas as pd
from pathlib import Path

def main():
    raw = pd.read_csv("/Users/alexmackenzie/projects/nba-career-analytics/data/raw/career_stats_2000_onward.csv")
    players = pd.read_csv("/Users/alexmackenzie/projects/nba-career-analytics/data/raw/players_2000_onward.csv")
    raw.columns = raw.columns.str.lower()
    players.columns = players.columns.str.lower()
    players = players.rename(columns={"person_id": "player_id", "display_first_last": "player_name"})
    players["player_id"] = players["player_id"].astype(int)

    agg = raw.groupby(["player_id", "season_id"]).agg({
        "team_abbreviation": lambda x: ",".join(sorted(set(x))),
        "player_age": "mean",
        "gp": "sum",
        "min": "sum",
        "fgm": "sum", "fga": "sum", "fg3m": "sum", "fg3a": "sum",
        "ftm": "sum", "fta": "sum",
        "oreb": "sum", "dreb": "sum", "reb": "sum",
        "ast": "sum", "stl": "sum", "blk": "sum",
        "tov": "sum", "pf": "sum", "pts": "sum",
    }).reset_index()

    agg["season"] = agg["season_id"].str[:4].astype(int)
    denom = (agg["fga"] + 0.44 * agg["fta"]).replace(0, pd.NA)
    agg["ts_pct"] = agg["pts"] / (2 * denom)
    agg["efg_pct"] = (agg["fgm"] + 0.5 * agg["fg3m"]) / agg["fga"].replace(0, pd.NA)
    agg["mp_per_g"] = agg["min"] / agg["gp"].replace(0, pd.NA)
    for col in ["pts", "reb", "ast"]:
        agg[f"{col}_per75"] = agg[col] / agg["min"].replace(0, pd.NA) * 75

    df = agg.merge(players[["player_id", "player_name", "position"]], on="player_id", how="left")

    # simple annotations
    df["annotation"] = None
    for pid, g in df.groupby("player_id"):
        ts_std = g["ts_pct"].std(ddof=0)
        if ts_std is None or ts_std == 0 or pd.isna(ts_std):
            # no variation; skip annotations
            continue
        z = (g["ts_pct"] - g["ts_pct"].mean()) / ts_std
        msg = pd.Series([None]*len(g), index=g.index)
        msg[z > 1.2] = "Elite efficiency year"
        msg[z < -1.2] = "Rough efficiency year"
        df.loc[g.index, "annotation"] = msg

    Path("/Users/alexmackenzie/projects/nba-career-analytics/data/clean").mkdir(parents=True, exist_ok=True)
    df.to_parquet("/Users/alexmackenzie/projects/nba-career-analytics/data/clean/player_seasons.parquet", index=False)
    print("Wrote /Users/alexmackenzie/projects/nba-career-analytics/data/clean/player_seasons.parquet", df.shape)

if __name__ == "__main__":
    main()
