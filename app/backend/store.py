import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from collections import Counter


class Store:
    def __init__(self):
        # Build absolute paths so uvicorn can be launched from any cwd.
        root = Path(__file__).resolve().parents[2]
        self.parquet = root / "data/clean/player_seasons.parquet"
        self.sim_path = root / "models/similarity.pkl"
        # Bio/position enrichment (CSV generated externally).
        self.positions_path = root / "data/clean/player_bio.csv"

        # Load full dataset into memory via pandas to avoid duckdb instabilities / segfaults.
        self.df = pd.read_parquet(self.parquet)
        # Derive per-game and composite fields
        self.df["pts_per_game"] = self.df["pts"] / self.df["gp"].replace({0: pd.NA})
        self.df["ast_per_game"] = self.df["ast"] / self.df["gp"].replace({0: pd.NA})
        self.df["reb_per_game"] = self.df["reb"] / self.df["gp"].replace({0: pd.NA})
        self.df["fg3_per_game"] = self.df["fg3m"] / self.df["gp"].replace({0: pd.NA})
        self.df["fg_pct"] = self.df["fgm"] / self.df["fga"].replace({0: pd.NA})
        self.df["ft_pct"] = self.df["ftm"] / self.df["fta"].replace({0: pd.NA})
        self.df["stl_per_game"] = self.df["stl"] / self.df["gp"].replace({0: pd.NA})
        self.df["blk_per_game"] = self.df["blk"] / self.df["gp"].replace({0: pd.NA})
        self.df["tov_per_game"] = self.df["tov"] / self.df["gp"].replace({0: pd.NA})
        self.df["mpg"] = self.df["min"] / self.df["gp"].replace({0: pd.NA})

        # Season-level z-scores for impact/load
        feat_for_z = [
            "pts_per_game",
            "ast_per_game",
            "reb_per_game",
            "stl_per_game",
            "blk_per_game",
            "ts_pct",
            "tov_per_game",
        ]
        season_stats = (
            self.df.groupby("season")[feat_for_z]
            .agg(["mean", "std"])
            .rename_axis(index="season")
        )

        def z_score(row, col):
            mean = season_stats.loc[row["season"], (col, "mean")]
            std = season_stats.loc[row["season"], (col, "std")]
            if pd.isna(std) or std == 0:
                return 0.0
            val = row[col]
            if pd.isna(val):
                return 0.0
            return (val - mean) / std

        for col in feat_for_z:
            self.df[f"z_{col}"] = self.df.apply(lambda r, c=col: z_score(r, c), axis=1)

        # Impact proxy
        self.df["impact_score"] = (
            self.df["z_pts_per_game"]
            + self.df["z_ast_per_game"]
            + self.df["z_reb_per_game"]
            + self.df["z_stl_per_game"]
            + self.df["z_blk_per_game"]
            + self.df["z_ts_pct"]
            - self.df["z_tov_per_game"]
        ) / 6

        # Availability and offensive load
        self.df["gp_share"] = (self.df["gp"] / 82).clip(0, 1)
        self.df["mpg_share"] = (self.df["mpg"] / 36).clip(lower=0, upper=1)
        self.df["availability"] = 0.6 * self.df["gp_share"] + 0.4 * self.df["mpg_share"]
        self.df["off_load"] = (self.df["z_pts_per_game"] + self.df["z_ast_per_game"]) / 2

        # Value score (no team context available, so last 10% omitted)
        self.df["value_score"] = (
            0.5 * self.df["impact_score"]
            + 0.25 * self.df["availability"]
            + 0.15 * self.df["off_load"]
        )

        # Count seasons with games played to filter short careers in the UI list.
        season_counts = (
            self.df[self.df["gp"] > 0]
            .groupby("player_id")["season"]
            .nunique()
            .rename("season_count")
        )
        seasons_played = (
            self.df[self.df["gp"] > 0]
            .groupby("player_id")["season"]
            .apply(lambda s: sorted(set(int(x) for x in s.tolist())))
            .rename("seasons_played")
        )

        self.players_df = (
            self.df.groupby(["player_id", "player_name", "position"], dropna=False)
            .agg(from_year=("season", "min"), to_year=("season", "max"))
            .reset_index()
        )
        self.players_df = self.players_df.merge(season_counts, on="player_id", how="left")
        self.players_df["season_count"] = self.players_df["season_count"].fillna(0).astype(int)
        self.players_df = self.players_df.merge(seasons_played, on="player_id", how="left")
        # Merge enriched positions (and height/weight) if available
        if self.positions_path.exists():
            if self.positions_path.suffix.lower() == ".parquet":
                pos_df = pd.read_parquet(self.positions_path)
            else:
                pos_df = pd.read_csv(self.positions_path)
            # Drop name to avoid duplicate column names after merge
            if "name" in pos_df.columns:
                pos_df = pos_df.drop(columns=["name"])
            # Align expected column names
            if "position" in pos_df.columns and "primary_position" not in pos_df.columns:
                pos_df = pos_df.rename(columns={"position": "primary_position"})
            self.players_df = self.players_df.merge(pos_df, on="player_id", how="left")
        else:
            self.players_df["primary_position"] = None

        # Align schema expectations
        self.players_df = self.players_df.rename(columns={"player_name": "name"})
        # Prefer enriched position
        self.players_df["position"] = self.players_df["primary_position"].fillna(self.players_df["position"])
        # Cast position and name to string to satisfy response model
        self.players_df["position"] = self.players_df["position"].astype(str)
        self.players_df["name"] = self.players_df["name"].astype(str)
        # Drop duplicate columns if any remain
        self.players_df = self.players_df.loc[:, ~self.players_df.columns.duplicated()]
        # Clean height/weight types
        if "height" in self.players_df.columns:
            self.players_df["height"] = self.players_df["height"].astype(str)
            self.players_df.loc[self.players_df["height"].isin(["nan", "None"]), "height"] = None
        if "weight" in self.players_df.columns:
            self.players_df["weight"] = pd.to_numeric(self.players_df["weight"], errors="coerce")
        self.season_count_by_id = dict(
            zip(self.players_df["player_id"].astype(int).tolist(), self.players_df["season_count"].astype(int).tolist())
        )
        self.sim = joblib.load(str(self.sim_path)) if self.sim_path.exists() else None
        self.sim_latest = None
        if self.sim:
            try:
                scaler = self.sim["scaler"]
                feat_df = self.sim["feature_df"]
                features = self.sim.get("features", [c for c in feat_df.columns if c not in ["player_id", "season"]])
                latest_feat = (
                    feat_df.sort_values("season")
                    .groupby("player_id", as_index=False)
                    .tail(1)
                    .copy()
                )
                Xn = scaler.transform(latest_feat[features])
                nn = NearestNeighbors(metric="euclidean")
                nn.fit(Xn)
                self.sim_latest = {
                    "nn": nn,
                    "scaler": scaler,
                    "features": features,
                    "player_ids": latest_feat["player_id"].astype(int).to_list(),
                    "latest_feat": latest_feat[["player_id"] + features].copy(),
                }
            except Exception as e:
                print(f"[sim_latest] build failed: {e}")
                self.sim_latest = None

        # Counting-stats similarity space (geometry of box score rates only).
        # Uses each player's peak-season row (season < 2025, gp > 0), where
        # "peak" is defined as the season with the highest MPG. This avoids
        # late-career/low-minute seasons dominating the similarity space.
        self.counting_sim = None
        self.counting_sim_error = None
        self._ensure_counting_sim()
        self._label_summary_cache = None
        self._forecast_cache = {}

    def _ensure_counting_sim(self):
        if self.counting_sim is not None:
            return
        try:
            pool = self.df[(self.df["season"] < 2025) & (self.df["gp"] > 0)].copy()
            # Use a modest games-played floor to reduce weird "peak" picks from
            # tiny samples. Falls back to all seasons for a player if needed.
            pool_sized = pool[pool["gp"] >= 20].copy()
            if pool_sized.empty:
                pool_sized = pool

            pool_sized["_mpg_for_peak"] = pool_sized["mpg"].fillna(0.0)
            idx = pool_sized.groupby("player_id")["_mpg_for_peak"].idxmax()
            peak = pool_sized.loc[idx].drop(columns=["_mpg_for_peak"]).copy()
            peak = peak.sort_values(["player_id", "season"])
            features = [
                "ts_pct",  # efficiency
                "fg3_per_game",  # threes
                "pts_per_game",  # points
                "reb_per_game",  # rebounds
                "ast_per_game",  # assists
                "stl_per_game",  # steals
                "blk_per_game",  # blocks
                "tov_per_game",  # turnovers
            ]
            X = peak[features].fillna(0.0)
            scaler = StandardScaler()
            Xn = scaler.fit_transform(X)
            nn = NearestNeighbors(metric="euclidean")
            nn.fit(Xn)
            norm = 1.0 / (1.0 + np.exp(-Xn))
            pids = peak["player_id"].astype(int).to_list()
            geometry_by_id = {pid: norm[i] for i, pid in enumerate(pids)}
            self.counting_sim = {
                "nn": nn,
                "scaler": scaler,
                "features": features,
                "player_ids": pids,
                "peak": peak[["player_id", "season"] + features].copy(),
                "geometry_by_id": geometry_by_id,
            }
        except Exception as e:
            # Keep the rest of the app running even if this optional model fails.
            self.counting_sim_error = str(e)
            print(f"[counting_sim] build failed: {e}")
            self.counting_sim = None

    def players(self):
        # Return full set; frontend can choose to filter (e.g., season_count >= 3).
        clean = self.players_df.replace({pd.NA: None, np.nan: None, np.inf: None, -np.inf: None})
        return clean.to_dict("records")

    def trajectory(self, player_id: int):
        g = self.df[(self.df.player_id == player_id) & (self.df.season < 2025)].copy()
        if g.empty:
            return []
        g = g.sort_values("season")
        cols = [
            "season",
            "player_age",
            "gp",
            "mpg",
            "pts_per_game",
            "ast_per_game",
            "reb_per_game",
            "fg3_per_game",
            "fg_pct",
            "ft_pct",
            "stl_per_game",
            "blk_per_game",
            "tov_per_game",
            "ts_pct",
            "value_score",
            "annotation",
        ]
        g = g[cols]
        g = g.rename(columns={"player_age": "age"})
        g = g.where(pd.notna(g), None)

        def tag_row(row):
            tags = []
            ts = row["ts_pct"] or 0
            pts = row["pts_per_game"] or 0
            ast = row["ast_per_game"] or 0
            reb = row["reb_per_game"] or 0
            fg3 = row["fg3_per_game"] or 0
            stl_blk = (row["stl_per_game"] or 0) + (row["blk_per_game"] or 0)
            blk = row["blk_per_game"] or 0
            gp = row["gp"] or 0
            mpg = row["mpg"] or 0
            val = row.get("value_score") or 0
            age = row.get("age") or 0

            if gp < 40:
                tags.append("LowGP")
            if mpg < 18:
                tags.append("LowMP")
            if pts > 26:
                tags.append(f"{pts:.1f}PPG"[:6])
            elif pts > 20:
                tags.append(f"{pts:.1f}PPG"[:6])
            if ts > 0.62:
                tags.append("TS62+")
            elif ts < 0.52:
                tags.append("TS<52")
            if fg3 > 2.5:
                tags.append(f"3PM{fg3:.1f}"[:7])
            if ast > 7:
                tags.append("AST7+")
            if reb > 10:
                tags.append("REB10+")
            if stl_blk > 2.0:
                tags.append("DEF2+")
            if blk > 1.5:
                tags.append("BLK1.5")
            if val > 1.0:
                tags.append("VAL1.0")
            if age > 30 and val < 0.2:
                tags.append("DECLINE")

            # Keep at most two short tags
            return " ".join(tags[:2]) if tags else None

        g["annotation"] = g.apply(tag_row, axis=1)
        return g.to_dict("records")

    def comps(self, player_id: int, k: int):
        # Prefer a player-level similarity space (one vector per player) for stability.
        if self.sim_latest:
            nn = self.sim_latest["nn"]
            scaler = self.sim_latest["scaler"]
            features = self.sim_latest["features"]
            latest_feat = self.sim_latest["latest_feat"]

            row = latest_feat[latest_feat.player_id == player_id]
            if row.empty:
                return []
            Xn = scaler.transform(row[features])
            dist, idx = nn.kneighbors(Xn, n_neighbors=min(k + 20, len(latest_feat)))

            out = []
            for d, i in zip(dist[0], idx[0]):
                pid = int(latest_feat.iloc[i].player_id)
                if pid == player_id:
                    continue
                if self.season_count_by_id.get(pid, 0) < 3:
                    continue
                name = self.players_df.loc[self.players_df.player_id == pid, "name"]
                out.append(
                    {
                        "player_id": pid,
                        "name": name.iloc[0] if not name.empty else "Unknown",
                        "distance": float(d),
                    }
                )
                if len(out) >= k:
                    break
            for idx_rank, item in enumerate(out, start=1):
                item["similarity_rank"] = idx_rank
            return out

        if not self.sim:
            return []
        scaler = self.sim["scaler"]
        nn = self.sim["nn"]
        feat_df = self.sim["feature_df"]
        features = self.sim.get("features", [c for c in feat_df.columns if c not in ["player_id", "season"]])
        row = feat_df[feat_df.player_id == player_id].tail(1)
        if row.empty:
            return []
        Xn = scaler.transform(row[features])
        # Grab extra neighbors then dedupe by player_id (feature_df has per-season rows)
        dist, idx = nn.kneighbors(Xn, n_neighbors=min(k + 20, len(feat_df)))
        seen = {}
        for d, i in zip(dist[0], idx[0]):
            pid = int(feat_df.iloc[i].player_id)
            if pid == player_id:
                continue
            # Keep comps aligned with the selectable player list (>= 3 seasons with games played).
            if self.season_count_by_id.get(pid, 0) < 3:
                continue
            # keep the closest season distance per player_id
            if pid not in seen or d < seen[pid]["distance"]:
                name = self.players_df.loc[self.players_df.player_id == pid, "name"]
                seen[pid] = {
                    "player_id": pid,
                    "name": name.iloc[0] if not name.empty else "Unknown",
                    "distance": float(d),
                }
            if len(seen) >= k:
                break
        sorted_res = sorted(seen.values(), key=lambda x: x["distance"])
        for idx_rank, item in enumerate(sorted_res, start=1):
            item["similarity_rank"] = idx_rank
        return sorted_res

    def comps_counting(self, player_id: int, k: int):
        self._ensure_counting_sim()
        if not self.counting_sim:
            raise RuntimeError(f"counting_sim unavailable: {self.counting_sim_error or 'unknown error'}")
        nn = self.counting_sim["nn"]
        scaler = self.counting_sim["scaler"]
        features = self.counting_sim["features"]
        player_ids = self.counting_sim["player_ids"]
        if player_id not in player_ids:
            return []

        g = (
            self.df[(self.df.player_id == player_id) & (self.df.season < 2025) & (self.df.gp > 0)]
            .sort_values("season")
            .tail(1)
        )
        if g.empty:
            return []
        Xn = scaler.transform(g[features].fillna(0.0))

        dist, idx = nn.kneighbors(Xn, n_neighbors=min(k + 50, len(player_ids)))
        out = []
        for d, i in zip(dist[0], idx[0]):
            pid = int(player_ids[i])
            if pid == player_id:
                continue
            if self.season_count_by_id.get(pid, 0) < 3:
                continue
            name = self.players_df.loc[self.players_df.player_id == pid, "name"]
            out.append(
                {
                    "player_id": pid,
                    "name": name.iloc[0] if not name.empty else "Unknown",
                    "distance": float(d),
                }
            )
            if len(out) >= k:
                break
        for idx_rank, item in enumerate(out, start=1):
            item["similarity_rank"] = idx_rank
        return out

    def counting_geometry(self, player_id: int, k: int):
        """
        Return normalized (0-1) 8-axis geometry values for the selected player
        and its top counting-stats comps. Similarity distance is Euclidean in
        standardized (z) space; we map z -> (0,1) via logistic for the UI.
        """
        self._ensure_counting_sim()
        if not self.counting_sim:
            raise RuntimeError(f"counting_sim unavailable: {self.counting_sim_error or 'unknown error'}")

        comps = self.comps_counting(player_id, k)
        ids = [player_id] + [c["player_id"] for c in comps]
        dist_by_id = {c["player_id"]: c["distance"] for c in comps}

        geometry_by_id = self.counting_sim.get("geometry_by_id") or {}

        def name_for(pid: int) -> str:
            name = self.players_df.loc[self.players_df.player_id == pid, "name"]
            return name.iloc[0] if not name.empty else str(pid)

        def row(pid: int):
            v = geometry_by_id.get(int(pid))
            if v is None:
                return None
            # features order is fixed above
            return {
                "player_id": int(pid),
                "name": name_for(int(pid)),
                "efficiency": float(v[0]),
                "threes": float(v[1]),
                "points": float(v[2]),
                "rebounds": float(v[3]),
                "assists": float(v[4]),
                "steals": float(v[5]),
                "blocks": float(v[6]),
                "turnovers": float(v[7]),
                "distance": float(dist_by_id.get(int(pid))) if int(pid) in dist_by_id else None,
            }

        series = []
        sel = row(player_id)
        if sel:
            series.append(sel)
        for c in comps:
            r = row(c["player_id"])
            if r:
                series.append(r)

        return {"series": series}

    def _label_for_player_group(self, g: pd.DataFrame) -> tuple[str, str | None]:
        """
        Return an "AI-ish" human-readable label based on career peaks/availability.
        This is intentionally heuristic and stable (no network/LLM dependency).
        """
        seasons_played = int(g["season"].nunique())

        # Peaks and averages to avoid bias to last healthy prime year
        peak_val = g["value_score"].max(skipna=True)
        peak_impact = g["impact_score"].max(skipna=True)
        peak_offload = g["off_load"].max(skipna=True)
        peak_pts75 = g["pts_per75"].max(skipna=True)
        peak_ts = g["ts_pct"].max(skipna=True)
        peak_pts_pg = g["pts_per_game"].max(skipna=True)
        peak_fg3_pg = g["fg3_per_game"].max(skipna=True)
        peak_reb_pg = g["reb_per_game"].max(skipna=True)
        peak_ast_pg = g["ast_per_game"].max(skipna=True)
        peak_stl_pg = g["stl_per_game"].max(skipna=True)
        peak_blk_pg = g["blk_per_game"].max(skipna=True)
        peak_stl_blk = (g["stl_per_game"] + g["blk_per_game"]).max(skipna=True)
        peak_mpg = g["mpg"].max(skipna=True)
        avg_availability = g["availability"].mean(skipna=True)
        latest_gp = g.sort_values("season").iloc[-1].gp if not g.empty else 0

        # Defaults if NaN
        def nz(x, default=0.0):
            return default if pd.isna(x) else float(x)

        peak_val = nz(peak_val)
        peak_impact = nz(peak_impact)
        peak_offload = nz(peak_offload)
        peak_pts75 = nz(peak_pts75)
        peak_ts = nz(peak_ts)
        peak_pts_pg = nz(peak_pts_pg)
        peak_fg3_pg = nz(peak_fg3_pg)
        peak_reb_pg = nz(peak_reb_pg)
        peak_ast_pg = nz(peak_ast_pg)
        peak_stl_pg = nz(peak_stl_pg)
        peak_blk_pg = nz(peak_blk_pg)
        peak_stl_blk = nz(peak_stl_blk)
        peak_mpg = nz(peak_mpg)
        avg_availability = nz(avg_availability)
        latest_gp = nz(latest_gp)

        is_franchise = peak_val > 1.2 and avg_availability > 0.65 and seasons_played >= 8
        is_star = peak_val > 0.9 and avg_availability > 0.55

        # High-level edge cases
        if seasons_played <= 2 and latest_gp < 30:
            return (
                "Developing prospect",
                f"{seasons_played} seasons played; latest GP={latest_gp:.0f}",
            )
        if avg_availability < 0.35 and (peak_val > 0.6 or peak_offload > 0.35):
            return (
                "Injury-limited talent",
                f"avg availability={avg_availability:.2f}; peak value={peak_val:.2f}",
            )

        # Archetype signals (peak season)
        playmaker = peak_ast_pg >= 7.5
        scorer = peak_pts_pg >= 24.0
        shooter = peak_fg3_pg >= 2.8
        rim_protector = peak_blk_pg >= 2.0
        stopper = peak_stl_pg >= 1.7 and peak_pts_pg < 16.0
        rebounder = peak_reb_pg >= 11.0
        three_and_d = peak_fg3_pg >= 1.8 and peak_stl_blk >= 2.0 and peak_pts_pg < 18.0
        stretch_big = peak_fg3_pg >= 1.6 and peak_reb_pg >= 6.5 and peak_blk_pg < 1.8

        label = "Depth piece"
        if is_franchise:
            label = "Franchise cornerstone"
        elif is_star and playmaker:
            label = "All-star playmaker"
        elif is_star and scorer and peak_ts >= 0.56:
            label = "All-star scorer"
        elif is_star:
            label = "Impact star"
        elif three_and_d:
            label = "3-and-D wing"
        elif rim_protector and peak_reb_pg >= 8.0:
            label = "Rim-protecting anchor"
        elif rebounder:
            label = "Glass-cleaning rebounder"
        elif stretch_big:
            label = "Stretch big"
        elif shooter and peak_pts_pg < 18.0:
            label = "3-point specialist"
        elif stopper:
            label = "Defensive stopper"
        elif peak_offload > 0.4 and avg_availability > 0.4 and peak_pts_pg > 12:
            label = "Scoring spark plug"
        elif peak_pts75 > 18 and peak_ts < 0.54:
            label = "Volume scorer"
        elif peak_val > 0.6 and avg_availability > 0.55:
            label = "High-value starter"
        elif peak_val > 0.3 and avg_availability > 0.45:
            label = "Reliable role player"

        rationale = (
            f"peak mpg={peak_mpg:.1f}, pts/g={peak_pts_pg:.1f}, ast/g={peak_ast_pg:.1f}, "
            f"reb/g={peak_reb_pg:.1f}, 3pm/g={peak_fg3_pg:.1f}, ts%={peak_ts:.3f}, "
            f"stl+blk={peak_stl_blk:.1f}, peak value={peak_val:.2f}, avg availability={avg_availability:.2f}"
        )
        return label, rationale

    def label(self, player_id: int):
        g = self.df[(self.df.player_id == player_id) & (self.df.season < 2025)]
        if g.empty:
            return {"label": "Unknown", "method": "heuristic"}
        label, rationale = self._label_for_player_group(g)
        return {"label": label, "method": "heuristic", "rationale": rationale}

    def label_summary(self):
        """
        Return counts of all labels across the player universe.
        Cached for the lifetime of the process (restarts recompute).
        """
        if self._label_summary_cache is not None:
            return self._label_summary_cache

        counts: Counter[str] = Counter()
        player_ids = self.players_df["player_id"].astype(int).tolist()
        for pid in player_ids:
            g = self.df[(self.df.player_id == pid) & (self.df.season < 2025)]
            if g.empty:
                continue
            label, _ = self._label_for_player_group(g)
            counts[label] += 1

        labels = [{"label": k, "count": int(v)} for k, v in counts.most_common()]
        self._label_summary_cache = {"total_players": int(sum(counts.values())), "labels": labels}
        return self._label_summary_cache

    def forecast(self, player_id: int):
        """
        Heuristic forecast for 2025 and 2026 seasonal success (value_score) with a 50% interval.
        Uses:
          - Regression to mean of last 2 seasons
          - Light aging curve (peak ~27, slow decline after 30)
          - Volatility from last 3 seasons to size the band
        Returns None if the player doesn't have a 2025 row in the data.
        """
        if player_id in self._forecast_cache:
            return self._forecast_cache[player_id]

        g = self.df[(self.df.player_id == player_id) & (self.df.season < 2025) & (self.df.gp > 0)].copy()
        has_2025 = (self.df[(self.df.player_id == player_id) & (self.df.season == 2025)]).shape[0] > 0
        if not has_2025 or g.empty:
            self._forecast_cache[player_id] = None
            return None

        g = g.sort_values("season")
        # Recent seasons for trend
        recent = g.tail(3)
        vals = recent["value_score"].dropna().tolist()
        if not vals:
            self._forecast_cache[player_id] = None
            return None

        # Regression to mean of last 2 seasons (weights 0.6 / 0.4)
        last_two = g.tail(2)["value_score"].fillna(method="ffill").fillna(method="bfill").tolist()
        if len(last_two) == 1:
            base = last_two[0]
            trend = 0.0
        else:
            base = 0.6 * last_two[-1] + 0.4 * last_two[-2]
            trend = last_two[-1] - last_two[-2]

        # Simple aging adjustment around age 27 peak
        last_age = float(g.iloc[-1]["player_age"]) if "player_age" in g.columns and pd.notna(g.iloc[-1]["player_age"]) else None
        age_adj_2025 = 0.0
        age_adj_2026 = 0.0
        if last_age is not None:
            def age_delta(age):
                if age < 23:
                    return 0.05
                if 23 <= age < 27:
                    return 0.02
                if 27 <= age < 30:
                    return -0.01
                if 30 <= age < 33:
                    return -0.04
                return -0.08
            age_adj_2025 = age_delta(last_age + 1)  # next season age
            age_adj_2026 = age_delta(last_age + 2)

        # Volatility-based band: center around median, width from recent std
        vol = float(np.std(vals)) if len(vals) > 1 else 0.08
        base_band = max(0.08, min(0.20, 0.6 * vol + 0.08))  # reasonable bounds

        forecasts = []
        # Build 2025 and 2026 with widening uncertainty
        for idx, (season, age_adj, widen) in enumerate(
            [(2025, age_adj_2025, 1.0), (2026, age_adj_2026, 1.35)]
        ):
            median = base + age_adj + (trend * 0.5 * idx)
            band_half = base_band * widen
            p25 = median - band_half / 2
            p75 = median + band_half / 2
            forecasts.append({"season": season, "median": float(median), "p25": float(p25), "p75": float(p75)})

        self._forecast_cache[player_id] = forecasts
        return forecasts

    def radar(self, player_id: int, k: int):
        comps = self.comps(player_id, k)
        ids = [player_id] + [c["player_id"] for c in comps]

        series = []
        for pid in ids:
            g = self.df[(self.df.player_id == pid) & (self.df.season < 2025) & (self.df.gp > 0)]
            if g.empty:
                continue
            r = g.sort_values("season").iloc[-1]
            name = self.players_df.loc[self.players_df.player_id == pid, "name"]
            series.append(
                {
                    "player_id": pid,
                    "name": name.iloc[0] if not name.empty else str(pid),
                    "pts_per_game": float(r.pts_per_game) if pd.notna(r.pts_per_game) else None,
                    "ast_per_game": float(r.ast_per_game) if pd.notna(r.ast_per_game) else None,
                    "reb_per_game": float(r.reb_per_game) if pd.notna(r.reb_per_game) else None,
                    "fg3_per_game": float(r.fg3_per_game) if pd.notna(r.fg3_per_game) else None,
                    "ts_pct": float(r.ts_pct) if pd.notna(r.ts_pct) else None,
                    "availability": float(r.availability) if pd.notna(r.availability) else None,
                    "value_score": float(r.value_score) if pd.notna(r.value_score) else None,
                }
            )
        return {"series": series}

    def projection(self, player_id: int):
        g = self.df[(self.df.player_id == player_id) & (self.df.season < 2025)].copy()
        if g.empty:
            return []
        # Only project if the player logged a 2024 season (as requested)
        g2024 = g[(g.season == 2024) & (g.gp > 0)]
        if g2024.empty:
            return []
        r = g.sort_values("season").iloc[-1]
        proj = []
        # Decay factors applied per projected year
        decay_pts_pg = -0.5
        decay_ast_pg = -0.2
        decay_reb_pg = -0.3
        decay_fg3_pg = -0.1
        decay_stl_pg = -0.05
        decay_blk_pg = -0.05
        decay_tov_pg = -0.05
        decay_ts = -0.005
        decay_gp = 0.07  # 7% fewer games per year
        decay_mp = 0.08  # 8% fewer minutes per year

        # Safe base stats (None if missing)
        base_gp = float(r.gp) if pd.notna(r.gp) else None
        base_mpg = float(r["min"]) / float(r.gp) if "min" in r and pd.notna(r["min"]) and pd.notna(r.gp) and r.gp else None
        base_pts_pg = float(r.pts) / float(r.gp) if pd.notna(r.pts) and pd.notna(r.gp) and r.gp else None
        base_ast_pg = float(r.ast) / float(r.gp) if pd.notna(r.ast) and pd.notna(r.gp) and r.gp else None
        base_reb_pg = float(r.reb) / float(r.gp) if pd.notna(r.reb) and pd.notna(r.gp) and r.gp else None
        base_fg3_pg = float(r.fg3m) / float(r.gp) if pd.notna(r.fg3m) and pd.notna(r.gp) and r.gp else None
        base_fg_pct = float(r.fgm) / float(r.fga) if pd.notna(r.fgm) and pd.notna(r.fga) and r.fga else None
        base_ft_pct = float(r.ftm) / float(r.fta) if pd.notna(r.ftm) and pd.notna(r.fta) and r.fta else None
        base_stl_pg = float(r.stl) / float(r.gp) if pd.notna(r.stl) and pd.notna(r.gp) and r.gp else None
        base_blk_pg = float(r.blk) / float(r.gp) if pd.notna(r.blk) and pd.notna(r.gp) and r.gp else None
        base_tov_pg = float(r.tov) / float(r.gp) if pd.notna(r.tov) and pd.notna(r.gp) and r.gp else None
        base_ts = float(r.ts_pct) if pd.notna(r.ts_pct) else None

        for i in range(1, 6):
            gp_pred = None
            if base_gp is not None:
                gp_pred = max(10, float(base_gp * (1 - decay_gp * i)))
            mpg_pred = None
            if base_mpg is not None:
                mpg_pred = max(5, float(base_mpg * (1 - decay_mp * i)))

            proj.append(
                {
                    "season": int(r.season + i),
                    "age": float(r.player_age + i) if pd.notna(r.player_age) else None,
                    "gp_pred": gp_pred,
                    "mpg_pred": mpg_pred,
                    "pts_per_game_pred": None if base_pts_pg is None else max(0, float(base_pts_pg + decay_pts_pg * i)),
                    "ast_per_game_pred": None if base_ast_pg is None else max(0, float(base_ast_pg + decay_ast_pg * i)),
                    "reb_per_game_pred": None if base_reb_pg is None else max(0, float(base_reb_pg + decay_reb_pg * i)),
                    "fg3_per_game_pred": None if base_fg3_pg is None else max(0, float(base_fg3_pg + decay_fg3_pg * i)),
                    "fg_pct_pred": base_fg_pct,
                    "ft_pct_pred": base_ft_pct,
                    "stl_per_game_pred": None if base_stl_pg is None else max(0, float(base_stl_pg + decay_stl_pg * i)),
                    "blk_per_game_pred": None if base_blk_pg is None else max(0, float(base_blk_pg + decay_blk_pg * i)),
                    "tov_per_game_pred": None if base_tov_pg is None else max(0, float(base_tov_pg + decay_tov_pg * i)),
                    "ts_pct_pred": None if base_ts is None else max(0, float(base_ts + decay_ts * i)),
                }
            )
        return proj


store = Store()
