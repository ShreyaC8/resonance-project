import math
import numpy as np
from app.clustering import get_feature_vector, gmm_model, cluster_probs, feature_matrix, labels, valid_ids
from app.database import Base, engine, SessionLocal
from app.models import Track
from app.schemas import TrackQueryResponse, RecRequest, RecResponse
from app.visualisations import coordinates, explained_variance, project_profile
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import AfterValidator
from sqlalchemy import select, func, distinct, or_, desc
from sqlalchemy.orm import Session
from sklearn.cluster import MiniBatchKMeans

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    "indie": ["indie", "indie-pop", "alternative", "alt-rock", "psych-rock", "garage"],
    "rock": ["rock", "alt-rock", "hard-rock", "punk-rock", "rock-n-roll", "grunge",
             "psych-rock", "garage", "british"],
    "pop": ["pop", "indie-pop", "synth-pop", "power-pop", "dance", "pop-film",
            "k-pop", "mandopop", "cantopop", "j-pop"],
    "electronic": ["electronic", "edm", "electro", "house", "techno", "idm",
                   "dubstep", "drum-and-base", "breakbeat", "industrial",
                   "chicago-house", "deep-house", "detroit-techno",
                   "minimal-techno", "progressive-house", "hardstyle",
                   "garage", "dance", "club", "trance"],
    "house": ["house", "deep-house", "chicago-house", "progressive-house",
              "electro", "garage"],
    "techno": ["techno", "detroit-techno", "minimal-techno", "electro", "idm",
               "industrial"],
    "trip-hop": ["trip-hop", "dub", "chill", "ambient"],
    "dubstep": ["dubstep", "drum-and-base", "breakbeat", "hardcore", "hardstyle"],
    "hip-hop": ["hip-hop", "r-n-b", "soul", "funk", "dancehall"],
    "r-n-b": ["r-n-b", "soul", "funk", "hip-hop", "gospel"],
    "metal": ["metal", "heavy-metal", "metalcore", "death-metal", "black-metal",
              "grindcore", "industrial", "goth"],
    "punk": ["punk", "punk-rock", "hardcore", "emo", "ska", "goth"],
    "jazz": ["jazz", "blues", "soul", "funk", "groove"],
    "blues": ["blues", "jazz", "soul", "gospel", "groove"],
    "folk": ["folk", "acoustic", "singer-songwriter", "songwriter", "bluegrass",
             "country", "guitar"],
    "country": ["country", "folk", "bluegrass", "honky-tonk", "rockabilly"],
    "classical": ["classical", "piano", "opera", "new-age", "romance", "show-tunes"],
    "latin": ["latin", "latino", "reggaeton", "salsa", "samba", "spanish",
              "brazil", "forro", "mpb", "pagode", "sertanejo", "tango"],
    "reggae": ["reggae", "dancehall", "dub", "ska"],
    "dance": ["dance", "edm", "house", "electro", "club", "party", "disco"],
    "trance": ["trance", "progressive-house", "hardstyle", "edm"],
    "world-music": ["world-music", "indian", "iranian", "turkish", "malay",
                     "afrobeats", "french", "german", "swedish"],
    "k-pop": ["k-pop", "j-pop", "mandopop", "cantopop", "pop"],
    "j-pop": ["j-pop", "j-rock", "j-idol", "j-dance", "anime"],
    "children": ["children", "kids", "disney", "comedy"],
    "mood": ["chill", "sleep", "study", "happy", "sad", "romance", "ambient",
             "new-age", "party", "comedy", "disney"],
}

GENRE_SCORES = {
    "indie": {
        "indie": 1.0, "indie-pop": 0.9, "alternative": 0.8, "alt-rock": 0.7,
        "psych-rock": 0.6, "garage": 0.5,
    },
    "rock": {
        "rock": 1.0, "alt-rock": 0.8, "hard-rock": 0.7, "punk-rock": 0.6,
        "rock-n-roll": 0.8, "grunge": 0.7, "psych-rock": 0.6, "garage": 0.5,
        "british": 0.5,
    },
    "pop": {
        "pop": 1.0, "indie-pop": 0.7, "synth-pop": 0.7, "power-pop": 0.6,
        "dance": 0.6, "pop-film": 0.6, "k-pop": 0.5, "mandopop": 0.5,
        "cantopop": 0.5, "j-pop": 0.5,
    },
    "electronic": {
        "electronic": 1.0, "edm": 0.8, "electro": 0.8, "house": 0.7,
        "techno": 0.7, "idm": 0.6, "dubstep": 0.6, "drum-and-base": 0.6,
        "breakbeat": 0.6, "industrial": 0.5, "chicago-house": 0.6,
        "deep-house": 0.6, "detroit-techno": 0.6, "minimal-techno": 0.6,
        "progressive-house": 0.7, "hardstyle": 0.6, "garage": 0.5,
        "dance": 0.6, "club": 0.5, "trance": 0.6,
    },
    "house": {
        "house": 1.0, "deep-house": 0.9, "chicago-house": 0.8,
        "progressive-house": 0.8, "electro": 0.6, "garage": 0.5,
    },
    "techno": {
        "techno": 1.0, "detroit-techno": 0.9, "minimal-techno": 0.8,
        "electro": 0.6, "idm": 0.5, "industrial": 0.5,
    },
    "trip-hop": {
        "trip-hop": 1.0, "dub": 0.6, "chill": 0.6, "ambient": 0.5,
    },
    "dubstep": {
        "dubstep": 1.0, "drum-and-base": 0.7, "breakbeat": 0.6,
        "hardcore": 0.5, "hardstyle": 0.6,
    },
    "hip-hop": {
        "hip-hop": 1.0, "r-n-b": 0.8, "soul": 0.6, "funk": 0.5,
        "dancehall": 0.5,
    },
    "r-n-b": {
        "r-n-b": 1.0, "soul": 0.8, "funk": 0.7, "hip-hop": 0.7, "gospel": 0.5,
    },
    "metal": {
        "metal": 1.0, "heavy-metal": 0.9, "metalcore": 0.7, "death-metal": 0.6,
        "black-metal": 0.6, "grindcore": 0.5, "industrial": 0.5, "goth": 0.5,
    },
    "punk": {
        "punk": 1.0, "punk-rock": 0.9, "hardcore": 0.7, "emo": 0.6,
        "ska": 0.5, "goth": 0.4,
    },
    "jazz": {
        "jazz": 1.0, "blues": 0.7, "soul": 0.6, "funk": 0.5, "groove": 0.5,
    },
    "blues": {
        "blues": 1.0, "jazz": 0.7, "soul": 0.6, "gospel": 0.5, "groove": 0.5,
    },
    "folk": {
        "folk": 1.0, "acoustic": 0.8, "singer-songwriter": 0.8,
        "songwriter": 0.8, "bluegrass": 0.7, "country": 0.6, "guitar": 0.6,
    },
    "country": {
        "country": 1.0, "folk": 0.6, "bluegrass": 0.7, "honky-tonk": 0.8,
        "rockabilly": 0.6,
    },
    "classical": {
        "classical": 1.0, "piano": 0.8, "opera": 0.7, "new-age": 0.5,
        "romance": 0.4, "show-tunes": 0.5,
    },
    "latin": {
        "latin": 1.0, "latino": 0.9, "reggaeton": 0.7, "salsa": 0.7,
        "samba": 0.6, "spanish": 0.6, "brazil": 0.6, "forro": 0.5,
        "mpb": 0.5, "pagode": 0.5, "sertanejo": 0.5, "tango": 0.5,
    },
    "reggae": {
        "reggae": 1.0, "dancehall": 0.8, "dub": 0.7, "ska": 0.6,
    },
    "dance": {
        "dance": 1.0, "edm": 0.8, "house": 0.7, "electro": 0.6,
        "club": 0.7, "party": 0.6, "disco": 0.6,
    },
    "trance": {
        "trance": 1.0, "progressive-house": 0.7, "hardstyle": 0.6, "edm": 0.6,
    },
    "world-music": {
        "world-music": 1.0, "indian": 0.6, "iranian": 0.6, "turkish": 0.6,
        "malay": 0.5, "afrobeats": 0.6, "french": 0.4, "german": 0.4,
        "swedish": 0.4,
    },
    "k-pop": {
        "k-pop": 1.0, "j-pop": 0.6, "mandopop": 0.5, "cantopop": 0.5,
        "pop": 0.6,
    },
    "j-pop": {
        "j-pop": 1.0, "j-rock": 0.7, "j-idol": 0.7, "j-dance": 0.6,
        "anime": 0.6,
    },
    "children": {
        "children": 1.0, "kids": 0.9, "disney": 0.6, "comedy": 0.4,
    },
    "mood": {
        "chill": 0.7, "sleep": 0.6, "study": 0.6, "happy": 0.6, "sad": 0.6,
        "romance": 0.5, "ambient": 0.6, "new-age": 0.5, "party": 0.5,
        "comedy": 0.4, "disney": 0.4,
    },
}

def get_related_genres(seed_genre):
    """Return the seed genre plus every genre that shares a category with it."""
    related = {seed_genre}
    for cat, members in RELATED_GENRES.items():
        if seed_genre == cat or seed_genre in members:
            related.add(cat)
            related.update(members)
    return related

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
        "valence": sum(t.valence for t in tracks) / num_of_tracks,
        "acousticness": sum(t.acousticness for t in tracks) / num_of_tracks,
        "instrumentalness": sum(t.instrumentalness for t in tracks) / num_of_tracks,
        "speechiness": sum(t.speechiness for t in tracks) / num_of_tracks,
        "tempo": sum(t.tempo for t in tracks) / num_of_tracks,
        "loudness": sum(t.loudness for t in tracks) / num_of_tracks
    }
    return profile

def calculate_catalogue_profile(matrix):
    mat_arr = np.array(matrix)
    result = np.mean(mat_arr, axis=0)
    return {
        "energy": float(result[0]),
        "danceability": float(result[1]),
        "valence": float(result[2]),
        "acousticness": float(result[3]),
        "instrumentalness": float(result[4]),
        "speechiness": float(result[5]),
        "tempo": float(result[6]),
        "loudness": float(result[7])
    }

def calculate_similarity(track, profile):
    distance = 0
    if track.energy is not None:
        distance += 0.2*abs(track.energy - profile["energy"])
    if track.danceability is not None:
        distance += 0.2*abs(track.danceability - profile["danceability"])
    if track.valence is not None:
        distance += 0.2*abs(track.valence - profile["valence"])
    if track.acousticness is not None:
        distance += 0.08*abs(track.acousticness - profile["acousticness"])
    if track.instrumentalness is not None:
        distance += 0.08*abs(track.instrumentalness - profile["instrumentalness"])
    if track.speechiness is not None:
        distance += 0.08*abs(track.speechiness - profile["speechiness"])
    if track.tempo is not None:
        distance += 0.08*abs((track.tempo - profile["tempo"]) / 243.372)
    if track.loudness is not None:
        distance += 0.08*abs((track.loudness - profile["loudness"]) - (-49.531)) / (4.532 - (-49.531))
    
    similarity = (1 - distance) * 100
    return similarity

def candidate_similarity(track1, track2):
    distance = (
        0.2*abs(track1.energy - track2.energy)
        + 0.2*abs(track1.danceability - track2.danceability)
        + 0.2*abs(track1.valence - track2.valence)
        + 0.08*abs(track1.acousticness - track2.acousticness)
        + 0.08*abs(track1.instrumentalness - track2.instrumentalness)
        + 0.08*abs(track1.speechiness - track2.speechiness)
        # Normalising the tempo and loudness to between 0 and 1
        + 0.08*abs((track1.tempo - track2.tempo) / 243.372)
        + 0.08*abs((track1.loudness - track2.loudness) - (-49.531)) / (4.532 - (-49.531))
    )
    return 1 - distance

def cosine_similarity(vector1, vector2):
    dot_product = sum(a * b for a,b in zip(vector1, vector2))

    magnitude1 = math.sqrt(sum(a ** 2 for a in vector1))
    magnitude2 = math.sqrt(sum(b ** 2 for b in vector2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    return dot_product / (magnitude1 * magnitude2)

def calc_cosine_similarity(track, profile):
    track_vector = get_feature_vector(track)
    profile_vector = [
        profile["energy"],
        profile["danceability"],
        profile["valence"],
        profile["acousticness"],
        profile["instrumentalness"],
        profile["speechiness"],
        # Normalised tempo and loudness values to match 0 to 1 range
        profile["tempo"] / 243.372,
        (profile["loudness"] - (-49.531)) / (4.532 - (-49.531))
    ]

    return cosine_similarity(track_vector, profile_vector) * 100

def candidate_cosine_similarity(track1, track2):
    vector1 = get_feature_vector(track1)
    vector2 = get_feature_vector(track2)

    return cosine_similarity(vector1, vector2)

def calculate_genre_score(candidate_genre, seed_genres):
    best_score = 0
    best_genre = None

    for seed_genre in seed_genres:
        # Find every category this seed genre belongs to (including itself, if it IS a category)
        categories = {
            cat for cat, members in RELATED_GENRES.items()
            if seed_genre == cat or seed_genre in members
        }
        #Take maximum as candidate song needs to be strongly related to one of user's interests to be a good discovery
        for cat in categories:
            score = GENRE_SCORES.get(cat, {}).get(candidate_genre, 0)
            if score > best_score:
                best_score = score
                best_genre = cat
    return best_score, best_genre

def mmr_rerank(candidates, limit, lambda_value=0.8, similarity_method="V2"):
    if similarity_method == "V2":
        candidate_sim_fn = candidate_similarity
    elif similarity_method == "V3":
        candidate_sim_fn = candidate_cosine_similarity
    else:
        raise ValueError("Invalid similarity method argument")

    # --- Dedup seed candidates by (track_name, artists) before scoring ---
    seen = set()
    deduped_candidates = []
    for candidate in candidates:
        track = candidate[0]
        key = (track.track_name, track.artists)
        if key in seen:
            continue
        seen.add(key)
        deduped_candidates.append(candidate)
    candidates = deduped_candidates

    selected = []

    while candidates and len(selected) < limit:
        best_track = None
        best_score = float("-inf")

        for candidate in candidates:
            track = candidate[0]
            relevance = candidate[1] / 100

            if not selected:
                diversity_penalty = 0
            else:
                diversity_penalty = max(
                    candidate_sim_fn(track, chosen[0])
                    for chosen in selected
                )

            mmr_score = (
                lambda_value * float(relevance) - (1 - lambda_value) * float(diversity_penalty)
            )

            if mmr_score > best_score:
                best_score = mmr_score
                best_track = candidate

        print(f"-> selected: {best_track[0].track_name!r} (score={best_score:.4f})\n")

        selected.append(best_track)
        candidates.remove(best_track)

    return selected

def audio_reasoning(similarity):
    if similarity >= 90:
        audio_reason = "Very similar audio characteristics"
    elif similarity >= 70:
        audio_reason = "Similar audio characteristics"
    else:
        audio_reason = "Somewhat similar audio characteristics"
    return audio_reason

def genre_reasoning(genre_score, matching_genre):
    if genre_score >= 0.7:
        genre_reason = f"genre closely related to your {matching_genre} taste"
    elif genre_score >= 0.4:
        genre_reason = f"genre somewhat related to your {matching_genre} taste"
    else:
        genre_reason = "genre less closely related to your selected tracks"
    return genre_reason

def evaluate_similarity_methods(request: RecRequest, db: Session = Depends(get_db)):
    #V2 is the 8-feature representation used to calculate similarity based on linear distance
    #V3 is the cosine version using vector representation 
    #Due to a lack of user preferences, this function shows how the models differ, not which is objectively better

    v2_results = get_recommendations(request, db, "V2")
    v3_results = get_recommendations(request, db, "V3")

    avg_rec_score_v2 = sum(v2_recommendation["score"] for v2_recommendation in v2_results) / len(v2_results)
    avg_rec_score_v3 = sum(v3_recommendation["score"] for v3_recommendation in v3_results) / len(v3_results)

    overlap_score = sum(
        rec["track_id"] in {v3["track_id"] for v3 in v3_results}
        for rec in v2_results
    )
    overlap_percentage = overlap_score / min(len(v2_results), len(v3_results)) * 100

    return {
        "v2_average_score": avg_rec_score_v2,
        "v3_average_score": avg_rec_score_v3,
        "overlap_count": overlap_score,
        "overlap_percentage": overlap_percentage
    }

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
    statement = select(Track.track_id, Track.track_name,Track.artists
                        ).where(or_(
                            Track.artists.contains(q),
                            Track.track_name.contains(q))
                        ).limit(limit)
    with SessionLocal() as db:
        track_options = db.execute(statement).all()
        if not track_options:
            raise HTTPException(status_code=404, detail="No matching results")
        return [
            {
                "track_id": track.track_id,
                "track_name": track.track_name,
                "artists": track.artists,
            }
            for track in track_options
        ]

''' app.post is used here as the server is being sent data to compute recommended tracks with'''
@app.post("/recommend", response_model=list[RecResponse])
def get_recommendations(
    request: RecRequest,
    db: Session = Depends(get_db),
    similarity_method="V2"
):
    if similarity_method == "V2":
        similarity_fn = calculate_similarity
    elif similarity_method == "V3":
        similarity_fn = calc_cosine_similarity
    else:
        raise ValueError("Invalid similarity method argument")

    track_ids = [track.track_id for track in request.tracks]
    recommendations = []

    seed_tracks = db.execute(
        select(Track).where(Track.track_id.in_(track_ids))
        ).scalars().all()

    if not seed_tracks:
        raise HTTPException(status_code=404, detail="No matching seed tracks")
    
    if any(
        t.energy is None or t.danceability is None or t.valence is None 
        for t in seed_tracks
        ):
        raise HTTPException(status_code=400,detail="Seed tracks must have energy, danceability, and valence")

    profile = calculate_profile(seed_tracks)

    '''Getting tracks in profile's cluster according to gmm'''
    profile_vector = [profile["energy"], 
                      profile["danceability"], 
                      profile["valence"],
                      profile["acousticness"], 
                      profile["instrumentalness"], 
                      profile["speechiness"],
                      profile["tempo"] / 243.372, 
                      (profile["loudness"] - (-49.531)) / (4.532 - (-49.531))]
    profile_membership = gmm_model.predict_proba([profile_vector])[0]
    print("Profile cluster membership:", profile_membership)

    MEMBERSHIP_THRESHOLD = 0.15  # tune this: lower = more permissive, more candidates included
    relevant_clusters = {
        i for i, prob in enumerate(profile_membership) if prob > MEMBERSHIP_THRESHOLD
    }
    print("Relevant clusters:", relevant_clusters)

    candidate_indices = [
        i for i in range(len(valid_ids))
        if any(cluster_probs[i][c] > MEMBERSHIP_THRESHOLD for c in relevant_clusters)
    ]
    same_cluster_ids = [valid_ids[i] for i in candidate_indices]

    '''Creating filter for similar genres to those of seed tracks'''
    seed_genres = set([t.track_genre for t in seed_tracks if t.track_genre is not None])

    genre_filter = {
        genre
        for seed_genre in seed_genres
        for genre in get_related_genres(seed_genre)
    }
    print("Genre filter:", genre_filter)

    '''Filtering tracks in same cluster that have similar genres to the seed tracks'''
    if not genre_filter:
        filtered_tracks = db.execute(
            select(Track).filter(Track.track_id.in_(same_cluster_ids))
            ).scalars().all()
    else:
        filtered_tracks = db.execute(
            select(Track)
            .filter((Track.track_id.in_(same_cluster_ids)) &
                    (Track.track_genre.in_(genre_filter)))
            ).scalars().all()

    for track in filtered_tracks:
        if track.track_id in track_ids:
            continue

        genre_score, matching_genre = calculate_genre_score(track.track_genre, seed_genres)
        similarity = similarity_fn(track, profile)
        final_score = 0.85*similarity + 0.15*(genre_score*100)

        audio_reason = audio_reasoning(similarity)
        genre_reason = genre_reasoning(genre_score, matching_genre)
        description = f"{audio_reason}, with a {genre_reason}"

        recommendations.append((track, final_score, description))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    print("Top 15 pre-MMR scores:")
    for track, final_score, description in recommendations[:15]:
        print(f"  {track.track_name!r} by {track.artists!r} score={final_score:.4f}")

    recommendations = mmr_rerank(recommendations, request.limit, similarity_method=similarity_method)

    return [
        {
            "track_id": track.track_id,
            "track_name": track.track_name,
            "artists": track.artists,
            "score": final_score,
            "reason" : description
        }
        for track, final_score, description in recommendations
    ]

@app.get("/genre")
def get_genres():
    with SessionLocal() as db:
        genres = db.execute(select(distinct(Track.track_genre))).scalars().all()
        return genres

def select_diverse_tracks(popular_ids, n_tracks=1500, n_regions=150):
    feature_array = np.asarray(feature_matrix)

    popular_id_set = set(popular_ids)

    remaining_indices = [
        index
        for index, track_id in enumerate(valid_ids)
        if track_id not in popular_id_set
    ]

    remaining_features = feature_array[remaining_indices]

    kmeans = MiniBatchKMeans(
        n_clusters=n_regions,
        random_state=42,
        n_init=3,
        batch_size=4096
    )

    region_labels = kmeans.fit_predict(remaining_features)

    selected_indices = []

    tracks_per_region = n_tracks // n_regions

    for region in range(n_regions):
        region_positions = np.where(region_labels == region)[0]

        region_indices = [
            remaining_indices[position]
            for position in region_positions
        ]

        centroid = kmeans.cluster_centers_[region]

        distances = [
            np.linalg.norm(feature_array[index] - centroid)
            for index in region_indices
        ]

        closest = np.argsort(distances)[:tracks_per_region]

        selected_indices.extend(
            region_indices[position]
            for position in closest
        )

    return [
        valid_ids[index]
        for index in selected_indices
    ]

@app.get("/taste-map")
def get_taste_map(seed_tracks: str | None = None, db: Session = Depends(get_db)):
    ordered_tracks = db.execute(
        select(Track).where(Track.track_id.in_(valid_ids)).order_by(desc(Track.popularity))
        .limit(3500)
        ).scalars().all()
    ordered_ids = [ordered_track.track_id for ordered_track in ordered_tracks]

    diverse_ids = select_diverse_tracks(ordered_ids)
    print(len(diverse_ids))
    diverse_tracks = db.execute(
        select(Track).where(Track.track_id.in_(diverse_ids))
        ).scalars().all()

    tracks = list(ordered_tracks+diverse_tracks)
    display_ids = ordered_ids + diverse_ids
    print(len(set(display_ids)) == 5000)
    track_lookup = {track.track_id: track for track in tracks}

    id_to_index = {
        track_id: index
        for index, track_id in enumerate(valid_ids)
    }
    result = []

    for track_id in display_ids:
        current_track = track_lookup.get(track_id)

        if current_track is None:
            continue

        index = id_to_index[current_track.track_id]

        result.append({
            "track_id": current_track.track_id,
            "track_name": current_track.track_name,
            "artists": current_track.artists,
            "genre": current_track.track_genre,
            "cluster": int(labels[index]),
            "x": float(coordinates[index][0]),
            "y": float(coordinates[index][1])
        })

    user_position = None

    if seed_tracks:
        print("TRACKS RECEIVED")
        track_ids = seed_tracks.split(",")

        user_tracks = db.execute(
            select(Track).where(Track.track_id.in_(track_ids))
            ).scalars().all()

        if user_tracks:
            profile = calculate_profile(user_tracks)
            profile_vector = [
                profile["energy"], 
                profile["danceability"], 
                profile["valence"],
                profile["acousticness"], 
                profile["instrumentalness"], 
                profile["speechiness"],
                profile["tempo"] / 243.372, 
                (profile["loudness"] - (-49.531)) / (4.532 - (-49.531))
            ]
            x, y = project_profile(profile_vector)

            user_position = {
                "x": float(x),
                "y": float(y)
            }

    return {
        "explained_variance": explained_variance.tolist(),
        "user_position": user_position,
        "tracks": result
    }

@app.get("/taste-dna")
def get_taste_dna(seed_tracks: str | None = None, db: Session = Depends(get_db)):
    if not seed_tracks:
        raise HTTPException(
            status_code=404,
            detail="No valid seed tracks found"
        )

    catalogue_profile = calculate_catalogue_profile(feature_matrix)

    track_ids = seed_tracks.split(",")
    
    user_tracks = db.execute(
        select(Track).where(Track.track_id.in_(track_ids))
        ).scalars().all()

    if not user_tracks:
        raise HTTPException(
            status_code=404,
            detail="No valid seed tracks found"
        )
    user_profile = calculate_profile(user_tracks)

    return {
        "user_profile": user_profile,
        "catalogue_profile": catalogue_profile
    }