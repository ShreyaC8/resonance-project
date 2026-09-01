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
        distance += 4*abs(track.energy - profile["energy"])
    if track.danceability is not None:
        distance += 3*abs(track.danceability - profile["danceability"])
    if track.valence is not None:
        distance += 3*abs(track.valence - profile["valence"])
    similarity = (1 - distance) * 100
    return distance, similarity

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
@app.post("/recommend", response_model = list[RecResponse])
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
        )
        .scalars()
        .all()
    )

    if not seed_tracks:
        raise HTTPException(status_code=404, detail="No matching seed tracks")

    profile = calculate_profile(seed_tracks)

    all_tracks = db.execute(select(Track)).scalars().all()

    for track in all_tracks:
        if track.track_id in track_ids:
            continue

        difference, similarity = calculate_similarity(track, profile)
        description = similarity_description(difference)

        recommendations.append(
            (track, similarity, description)
        )

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
'''def get_recommendations(request: RecRequest):
    track_ids = []
    recommendations = []
    response = []

    for track in request.tracks:
        track_ids.append(track.track_id)

    with SessionLocal() as db:
        seed_tracks = db.execute(select(Track).where(Track.track_id.in_(track_ids))).scalars().all()
        profile = calculate_profile(seed_tracks)

        all_tracks = db.execute(select(Track)).scalars().all()
        for track in all_tracks:
            #Ensure entered tracks do not appear as recommendations
            if track.track_id in track_ids:
                continue

            difference, similarity = calculate_similarity(track, profile)
            description = similarity_description(difference)
            recommendations.append((track, similarity, description))
        
        recommendations.sort(reverse=True, key=key_helper)
        recommendations = recommendations[:request.limit]
        
        if not recommendations:
            return 'No tracks recommended'
                
        for (track, similarity, description) in recommendations:
            response.append({
                "track_id": track.track_id,
                "track_name": track.track_name,
                "artists": track.artists,
                "score": similarity,
                "reason": description
            })
                
        return response    
'''

'''
    recommendations = []
    response = []
    statement = select(Track)

     Method to compare genre can be more sophisticated 
    (e.g. pop fans may enjoy indie pop)
    Maybe use string matching to filter related genres as an improvement
    if request.genre is not None:
        statement = statement.filter(Track.track_genre == request.genre)

    with SessionLocal() as db:
        tracks = db.execute(statement).scalars().all()
        for track in tracks:
            This section requires weighting to improve recommendation predictions
            score = 0

            if request.energy is not None:
                score += abs(track.energy - request.energy)

            if request.danceability is not None:
                score += abs(track.danceability - request.danceability)

            if request.valence is not None:
                score += abs(track.valence - request.valence)

            #Popularity needs to be normalised from 0-100 to 0-1
            if request.popularity is not None:
                score += 0.01*abs(track.popularity - request.popularity)

            recommendations.append((track, score))

        recommendations.sort(key=key_helper)
        recommendations = recommendations[:request.limit]

        if not recommendations:
            return 'No tracks recommended'
        
        for (track, score) in recommendations:
            response.append({
                "track_id": track.track_id,
                "track_name": track.track_name,
                "artists": track.artists,
                "score": score
            })
        
        return response
'''

@app.get("/genre")
def get_genres():
    with SessionLocal() as db:
        genres = db.execute(select(distinct(Track.track_genre))).scalars().all()
        return genres