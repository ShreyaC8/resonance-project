import pandas as pd

from app.database import Base, engine, SessionLocal
from app.models import Track

def load_dataset(dataset):
    data = pd.read_csv(dataset)
    return data

def import_tracks(dataframe, database):
    for row in dataframe.itertuples():
        current_track = Track(track_id = row.track_id,
                            track_name = row.track_name,
                            artists = row.artists,
                            album_name = row.album_name,
                            track_genre = row.track_genre,
                            popularity = row.popularity,
                            duration_ms = row.duration_ms,
                            explicit = row.explicit,
                            energy = row.energy,
                            danceability = row.danceability,
                            valence = row.valence,
                            key = row.key,
                            loudness = row.loudness,
                            mode = row.mode,
                            speechiness = row.speechiness,
                            acousticness = row.acousticness,
                            instrumentalness = row.instrumentalness,
                            liveness = row.liveness,
                            tempo = row.tempo,
                            time_signature = row.time_signature
                            )
        database.add(current_track)
    database.commit()
    return len(dataframe)

def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    df = load_dataset("data/spotifydatabase.csv")
    num_of_imports = import_tracks(df, db)
    db.close()
    print(f"Loaded {num_of_imports} songs")
