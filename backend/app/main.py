from.database import Base, engine, SessionLocal
from.models import Track
from.schemas import TrackQueryResponse, RecRequest
from fastapi import FastAPI, Query
from typing import Annotated
from pydantic import AfterValidator
from sqlalchemy import select, func

app = FastAPI()

sort_options = {
        "track_id": Track.track_id,
        "name": Track.track_name,
        "artists": Track.artists,
        "genre": Track.track_genre,
        "popularity": Track.popularity,
        "energy": Track.energy,
        "danceability": Track.danceability,
        "valence": Track.valence
    }

genre_options = [
        "acoustic", "afrobeats", "alt-rock", "alternative", "ambient", "anime",
        "black-metal", "bluegrass", "blues", "brazil", "breakbeat", "british",
        "cantopop", "chicago-house", "children", "chill", "classical", "club",
        "comedy", "country", "dance", "dancehall", "death-metal", "deep-house",
        "detroit-techno", "disco", "disney", "drum-and-base", "dub", "dubstep",
        "edm", "electro", "electronic", "emo", "folk", "forro",
        "french", "funk", "garage", "german", "gospel", "goth",
        "grindcore", "groove", "grunge", "guitar", "happy", "hard-rock",
        "hardcore", "hardstyle", "heavy-metal", "hip-hop", "honky-tonk", "house",
        "idm", "indian", "indie", "indie-pop", "industrial", "iranian",
        "j-dance", "j-idol", "j-pop", "j-rock", "jazz", "k-pop",
        "kids", "latin", "latino", "malay", "mandopop", "metal",
        "metalcore", "minimal-techno", "mpb", "new-age", "opera", "pagode",
        "party", "piano", "pop", "pop-film", "power-pop", "progressive-house",
        "psych-rock", "punk", "punk-rock", "r-n-b", "reggae", "reggaeton",
        "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa",
        "samba", "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep",
        "songwriter", "soul", "spanish", "study", "swedish", "synth-pop",
        "tango", "techno", "trance", "trip-hop", "turkish", "world-music"
    ]

def check_sort_opt(option: str):
    if option not in sort_options:
        raise ValueError('Invalid option')
    else:
        return option

def check_genre(genre: str):
    if genre not in genre_options:
        raise ValueError('Invalid genre')
    else:
        return genre

def key_helper(scored_track):
    return scored_track[1]

@app.get("/")
def basic_message():
    return {"message": "Resonance API is running"}

@app.get("/tracks", response_model = TrackQueryResponse)
def get_tracks(
    limit: int = Query(50, ge = 1, le = 100),
    offset: int = Query(0, ge = 0),
    sort_by: Annotated[str | None, AfterValidator(check_sort_opt)] = None,
    genre: Annotated[str | None, AfterValidator(check_genre)] = None, 
    min_energy: float | None = Query(None, ge = 0.0, le = 1.0),
    max_energy: float | None = Query(None, ge = 0.0, le = 1.0),
    min_danceability: float | None = Query(None, ge = 0.0, le = 1.0),
    max_danceability: float | None = Query(None, ge = 0.0, le = 1.0),
    min_valence: float | None = Query(None, ge = 0.0, le = 1.0),
    max_valence: float | None = Query(None, ge = 0.0, le = 1.0),
    min_popularity: int | None = Query(None, ge = 0, le = 100),
    max_popularity: int | None = Query(None, ge = 0, le = 100)
    ):

    filters = []

    if genre is not None:
        filters.append(Track.track_genre == genre)

    if min_energy is not None:
        filters.append(Track.energy >= min_energy)

    if max_energy is not None:
        filters.append(Track.energy <= max_energy)

    if min_danceability is not None:
        filters.append(Track.danceability >= min_danceability)
    
    if max_danceability is not None:
        filters.append(Track.danceability <= max_danceability)

    if min_valence is not None:
        filters.append(Track.valence >= min_valence)
    
    if max_valence is not None:
        filters.append(Track.valence <= max_valence)

    if min_popularity is not None:
        filters.append(Track.popularity >= min_popularity)
        
    if max_popularity is not None:
        filters.append(Track.popularity <= max_popularity)

    if sort_by is not None:
        statement = select(Track).where(*filters).order_by(sort_options[sort_by]).limit(limit).offset(offset)
    else:
        statement = select(Track).where(*filters).limit(limit).offset(offset)

    num_track_statement = select(func.count()).select_from(Track).where(*filters)

    with SessionLocal() as db:
        count_track_result = db.execute(num_track_statement).scalar()
        track_result = db.execute(statement).scalars().all()
        result = {
            "tracks": track_result, 
            "total": count_track_result, 
            "limit": limit, 
            "offset": offset,
            "sort_by": sort_by
        }
        return result

@app.get("/recommend")
def get_recommendations(request: RecRequest):
    recommendations = []

    ''' Method to compare genre can be more sophisticated 
    (e.g. pop fans may enjoy indie pop)
    Maybe use string matching to filter related genres as an improvement'''
    if request.genre is not None:
        statement = select(Track).filter(Track.track_genre == request.genre)
    else:
        statement = select(Track)

    with SessionLocal() as db:
        tracks = db.execute(statement).scalars().all()
        for track in tracks:
            score = 0

            if request.energy is not None:
                score += abs(track.energy - request.energy)

            if request.danceability is not None:
                score += abs(track.danceability - request.danceability)

            if request.valence is not None:
                score += abs(track.valence - request.valence)

            recommendations.append((track, score))

        recommendations = recommendations.sort(key=key_helper)[:request.limit]

        return recommendations