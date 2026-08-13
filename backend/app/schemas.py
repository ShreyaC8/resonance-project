from pydantic import BaseModel, ConfigDict, Field

class TrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id : str
    track_name : str
    artists : str
    track_genre : str
    popularity : int
    energy : float
    danceability : float
    valence : float

class TrackQueryResponse(BaseModel):
    tracks : list[TrackResponse]
    total : int
    limit : int
    offset : int

class RecRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    genre: str | None = None
    energy: float | None = Field(None, ge=0.0, le=1.0)
    danceability: float | None = Field(None, ge=0.0, le=1.0)
    valence: float | None = Field(None, ge=0.0, le=1.0)
    popularity: float | None = Field(None, ge=0.0, le=100)
    limit: int = Field(10, ge=1, le=50)