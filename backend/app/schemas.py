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

class TrackInput(BaseModel):
    track_id: str
    track_name: str
    artists: str

class RecRequest(BaseModel):
    tracks: list[TrackInput] = Field(min_length = 1, max_length = 5)
    limit: int = Field(default = 10, ge = 1, le = 50)

class RecResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id : str
    track_name : str
    artists : str
    score : float
    reason : str
