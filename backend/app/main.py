import numpy as np
from app.database import Base, engine, SessionLocal
from app.models import Track
from app.schemas import TrackQueryResponse, RecRequest, RecResponse
from fastapi import FastAPI, Query, Depends, HTTPException
from typing import Annotated
from pydantic import AfterValidator
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

app = FastAPI()

#For unit testing:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

GENRE_OPTIONS = [
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

RELATED_GENRES = {
    "indie": ["indie", "indie-pop", "alternative", "alt-rock", "psych-rock"],
    "rock": ["rock", "alt-rock", "hard-rock", "punk-rock", "rock-n-roll", "grunge"],
    "pop": ["pop", "indie-pop", "synth-pop", "power-pop", "dance"],
    "electronic": ["electronic", "edm", "electro", "house", "techno", "idm"],
    "house": ["house", "deep-house", "chicago-house", "progressive-house", "electro"],
    "techno": ["techno", "detroit-techno", "minimal-techno", "electro"],
    "hip-hop": ["hip-hop", "r-n-b", "soul", "funk"],
    "r-n-b": ["r-n-b", "soul", "funk", "hip-hop"],
    "metal": ["metal", "heavy-metal", "metalcore", "death-metal", "black-metal", "grindcore"],
    "punk": ["punk", "punk-rock", "hardcore", "emo", "ska"],
    "jazz": ["jazz", "blues", "soul", "funk"],
    "blues": ["blues", "jazz", "soul", "gospel"],
    "folk": ["folk", "acoustic", "singer-songwriter", "songwriter", "bluegrass", "country"],
    "country": ["country", "folk", "bluegrass", "honky-tonk", "rockabilly"],
    "classical": ["classical", "piano", "opera", "new-age"],
    "latin": ["latin", "latino", "reggaeton", "salsa", "samba", "spanish"],
    "reggae": ["reggae", "dancehall", "dub", "ska"],
    "dance": ["dance", "edm", "house", "electro", "club", "party"],
    "trance": ["trance", "progressive-house", "hardstyle", "edm"],
    "world-music": ["world-music", "indian", "iranian", "turkish", "malay", "afrobeats"],
    "k-pop": ["k-pop", "j-pop", "mandopop", "cantopop", "pop"],
    "j-pop": ["j-pop", "j-rock", "j-idol", "j-dance", "anime"],
}

GENRE_SCORES = {
    "indie": {
        "indie": 1.0,
        "indie-pop": 0.9,
        "alternative": 0.8,
        "alt-rock": 0.7,
        "psych-rock": 0.6,
    },
    "rock": {
        "rock": 1.0,
        "alt-rock": 0.8,
        "hard-rock": 0.7,
        "punk-rock": 0.6,
        "rock-n-roll": 0.8,
        "grunge": 0.7,
    },
    "pop": {
        "pop": 1.0,
        "indie-pop": 0.7,
        "synth-pop": 0.7,
        "power-pop": 0.6,
        "dance": 0.6,
    },
    "electronic": {
        "electronic": 1.0,
        "edm": 0.8,
        "electro": 0.8,
        "house": 0.7,
        "techno": 0.7,
        "idm": 0.6,
    },
    "house": {
        "house": 1.0,
        "deep-house": 0.9,
        "chicago-house": 0.8,
        "progressive-house": 0.8,
        "electro": 0.6,
    },
    "techno": {
        "techno": 1.0,
        "detroit-techno": 0.9,
        "minimal-techno": 0.8,
        "electro": 0.6,
    },
    "hip-hop": {
        "hip-hop": 1.0,
        "r-n-b": 0.8,
        "soul": 0.6,
        "funk": 0.5,
    },
    "r-n-b": {
        "r-n-b": 1.0,
        "soul": 0.8,
        "funk": 0.7,
        "hip-hop": 0.7,
    },
    "metal": {
        "metal": 1.0,
        "heavy-metal": 0.9,
        "metalcore": 0.7,
        "death-metal": 0.6,
        "black-metal": 0.6,
        "grindcore": 0.5,
    },
    "punk": {
        "punk": 1.0,
        "punk-rock": 0.9,
        "hardcore": 0.7,
        "emo": 0.6,
        "ska": 0.5,
    },
    "jazz": {
        "jazz": 1.0,
        "blues": 0.7,
        "soul": 0.6,
        "funk": 0.5,
    },
    "blues": {
        "blues": 1.0,
        "jazz": 0.7,
        "soul": 0.6,
        "gospel": 0.5,
    },
    "folk": {
        "folk": 1.0,
        "acoustic": 0.8,
        "singer-songwriter": 0.8,
        "songwriter": 0.8,
        "bluegrass": 0.7,
        "country": 0.6,
    },
    "country": {
        "country": 1.0,
        "folk": 0.6,
        "bluegrass": 0.7,
        "honky-tonk": 0.8,
        "rockabilly": 0.6,
    },
    "classical": {
        "classical": 1.0,
        "piano": 0.8,
        "opera": 0.7,
        "new-age": 0.5,
    },
    "latin": {
        "latin": 1.0,
        "latino": 0.9,
        "reggaeton": 0.7,
        "salsa": 0.7,
        "samba": 0.6,
        "spanish": 0.6,
    },
    "reggae": {
        "reggae": 1.0,
        "dancehall": 0.8,
        "dub": 0.7,
        "ska": 0.6,
    },
    "dance": {
        "dance": 1.0,
        "edm": 0.8,
        "house": 0.7,
        "electro": 0.6,
        "club": 0.7,
        "party": 0.6,
    },
    "trance": {
        "trance": 1.0,
        "progressive-house": 0.7,
        "hardstyle": 0.6,
        "edm": 0.6,
    },
    "world-music": {
        "world-music": 1.0,
        "indian": 0.6,
        "iranian": 0.6,
        "turkish": 0.6,
        "malay": 0.5,
        "afrobeats": 0.6,
    },
    "k-pop": {
        "k-pop": 1.0,
        "j-pop": 0.6,
        "mandopop": 0.5,
        "cantopop": 0.5,
        "pop": 0.6,
    },
    "j-pop": {
        "j-pop": 1.0,
        "j-rock": 0.7,
        "j-idol": 0.7,
        "j-dance": 0.6,
        "anime": 0.6,
    },
}

def check_sort_opt(option: str):
    if option not in sort_options:
        raise ValueError('Invalid option')
    else:
        return option

def check_genre(genre: str):
    if genre not in GENRE_OPTIONS:
        raise ValueError('Invalid genre')
    else:
        return genre

# Used lambda funct instead, no longer needed
def key_helper(scored_track):
    return scored_track[1]

def calculate_profile(tracks):
    num_of_tracks = len(tracks)
    profile = {
        "energy": sum(t.energy for t in tracks) / num_of_tracks,
        "danceability": sum(t.danceability for t in tracks) / num_of_tracks,
        "valence": sum(t.valence for t in tracks) / num_of_tracks
    }
    return profile

def calculate_similarity(track, profile):
    distance = 0
    if track.energy is not None:
        distance += 0.4*abs(track.energy - profile["energy"])
    if track.danceability is not None:
        distance += 0.3*abs(track.danceability - profile["danceability"])
    if track.valence is not None:
        distance += 0.3*abs(track.valence - profile["valence"])
    similarity = (1 - distance) * 100
    return distance, similarity

def calculate_genre_score(candidate_genre, seed_genres):
    scores = []
    for seed_genre in seed_genres:
        score = GENRE_SCORES.get(seed_genre, {}).get(candidate_genre, 0)
        scores.append(score)
    #Take maximum as candidate song needs to be strongly related to one of user's interests to be a good discovery
    return max(scores, default=0)

def similarity_description(difference):
    if difference < 0.05:
        return "Very similar"
    if difference < 0.15:
        return "Similar"
    if difference < 0.30:
        return "Somewhat different"
    return "Very different"

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

@app.get("/tracks/search")
def search_tracks(q: str = Query(min_length=1), limit: int = Query(10, ge=1, le=50)):
    statement = select(Track.track_id, Track.track_name, Track.artists).where(Track.artists.contains(str) or Track.track_name.contains(str)).limit(limit)
    with SessionLocal() as db:
        track_options = db.execute(statement).scalars().all()
        if not track_options:
            return ValueError("No matching results")
        return track_options

''' app.post is used here as the server is being sent data to compute recommended tracks with'''
@app.post("/recommend", response_model=list[RecResponse])
def get_recommendations(
    request: RecRequest,
    db: Session = Depends(get_db)
):
    track_ids = [track.track_id for track in request.tracks]
    recommendations = []

    seed_tracks = (
        db.execute(
            select(Track).where(Track.track_id.in_(track_ids))
            ).scalars().all()
    )

    if not seed_tracks:
        raise HTTPException(status_code=404, detail="No matching seed tracks")

    profile = calculate_profile(seed_tracks)

    seed_genres = set([t.genre for t in seed_tracks])

    similar_genres = np.array([
        RELATED_GENRES.get(seed_genre, [seed_genre])
        for seed_genre in seed_genres
        ])

    genre_filter = np.unique(similar_genres)

    gen_filtered_tracks = db.execute(
        select(Track).filter(Track.genre.in_(genre_filter))
        ).scalars().all()

    for track in gen_filtered_tracks:
        if track.track_id in track_ids:
            continue

        genre_score = calculate_genre_score(track.genre, seed_genres)
        difference, similarity = calculate_similarity(track, profile)
        final_score = 0.85*similarity + 0.15*(genre_score*100)

        description = similarity_description(difference)

    
        recommendations.append((track, final_score, description))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    recommendations = recommendations[:request.limit]

    return [
        {
            "track_id": track.track_id,
            "track_name": track.track_name,
            "artists": track.artists,
            "score": similarity,
            "reason": description
        }
        for track, similarity, description in recommendations
    ]

@app.get("/genre")
def get_genres():
    with SessionLocal() as db:
        genres = db.execute(select(distinct(Track.track_genre))).scalars().all()
        return genres