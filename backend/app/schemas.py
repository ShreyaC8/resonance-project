from pydantic import BaseModel, ConfigDict

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