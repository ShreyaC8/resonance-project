import pandas as pd
import sqlalchemy.exc

from app.database import Base, engine, SessionLocal
from app.models import Track
from sqlalchemy.exc import SQLAlchemyError

def load_dataset(dataset):
    try:
        return pd.read_csv(dataset)
    except FileNotFoundError:
        print("File not found")

def import_tracks(dataframe, database):
    import_amt = 0
    for row in dataframe.itertuples():
        current_track = Track(
            track_id = row.track_id,
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
            time_signature = row.time_signature)
        database.add(current_track)
        import_amt += 1
    try:
        database.commit()
        return import_amt
    except SQLAlchemyError as e:
        database.rollback()
        print(f"Import failed: {e}")
        return 0

def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    df = load_dataset("data/spotifydb_clean.csv")
    if df is not None:
        num_of_imports = import_tracks(df, db)
        print(f"Loaded {num_of_imports} songs")
    db.close()

if __name__ == "__main__":
    main()