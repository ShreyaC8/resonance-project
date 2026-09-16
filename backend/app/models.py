from sqlalchemy import Column, Integer, Float, String, Boolean
from app.database import Base

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)

    # Metadata
    track_id = Column(String)
    track_name = Column(String)
    artists = Column(String)
    album_name = Column(String)
    track_genre = Column(String)

    # Track Information
    popularity = Column(Integer)
    duration_ms = Column(Integer)
    explicit = Column(Boolean)

    # Features
    energy = Column(Float)
    danceability = Column(Float)
    valence = Column(Float)
    key = Column(Integer)
    loudness = Column(Float)
    mode = Column(Integer)
    speechiness = Column(Float)
    acousticness = Column(Float)
    instrumentalness = Column(Float)
    liveness = Column(Float)
    tempo = Column(Float)
    time_signature = Column(Integer)