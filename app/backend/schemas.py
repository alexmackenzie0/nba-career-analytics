from pydantic import BaseModel


class PlayerListItem(BaseModel):
    player_id: int
    name: str
    position: str | None = None
    from_year: int | None = None
    to_year: int | None = None
    season_count: int | None = None
    seasons_played: list[int] | None = None


class TrajectoryPoint(BaseModel):
    season: int
    age: float | None
    gp: float | None
    mpg: float | None
    pts_per_game: float | None
    ast_per_game: float | None
    reb_per_game: float | None
    fg3_per_game: float | None
    fg_pct: float | None
    ft_pct: float | None
    stl_per_game: float | None
    blk_per_game: float | None
    tov_per_game: float | None
    ts_pct: float | None
    value_score: float | None
    annotation: str | None = None


class SimilarPlayer(BaseModel):
    player_id: int
    name: str
    distance: float
    similarity_rank: int


class EmbeddingPoint(BaseModel):
    player_id: int
    name: str
    x: float
    y: float
    distance: float | None = None


class EmbeddingResponse(BaseModel):
    player: EmbeddingPoint | None
    comps: list[EmbeddingPoint]


class RadarSeries(BaseModel):
    player_id: int
    name: str
    pts_per_game: float | None = None
    ast_per_game: float | None = None
    reb_per_game: float | None = None
    fg3_per_game: float | None = None
    ts_pct: float | None = None
    availability: float | None = None
    value_score: float | None = None


class RadarResponse(BaseModel):
    series: list[RadarSeries]


class LabelResponse(BaseModel):
    label: str
    rationale: str | None = None
    method: str


class ProjectionPoint(BaseModel):
    season: int
    age: float | None
    gp_pred: float | None
    mpg_pred: float | None
    pts_per_game_pred: float | None
    ast_per_game_pred: float | None
    reb_per_game_pred: float | None
    fg3_per_game_pred: float | None
    fg_pct_pred: float | None
    ft_pct_pred: float | None
    stl_per_game_pred: float | None
    blk_per_game_pred: float | None
    tov_per_game_pred: float | None
    ts_pct_pred: float | None
