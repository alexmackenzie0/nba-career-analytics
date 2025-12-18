import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import joblib


def main():
    parquet_path = Path("data/clean/player_seasons.parquet")
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing {parquet_path}, run scripts/prepare_player_seasons.py first")

    df = pd.read_parquet(parquet_path)
    features = ["pts_per75", "ast_per75", "reb_per75", "ts_pct", "mp_per_g"]
    feat_df = df.dropna(subset=features).copy()
    X = feat_df[features]
    scaler = StandardScaler().fit(X)
    Xn = scaler.transform(X)

    nn = NearestNeighbors(n_neighbors=6, metric="euclidean").fit(Xn)
    Path("models").mkdir(exist_ok=True)
    joblib.dump(
        {"scaler": scaler, "nn": nn, "feature_df": feat_df[["player_id", "season"] + features], "features": features},
        "models/similarity.pkl",
    )
    print("Saved models/similarity.pkl")


if __name__ == "__main__":
    main()
