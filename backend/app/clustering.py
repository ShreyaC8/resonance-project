import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from app.database import Base, engine, SessionLocal
from app.models import Track

def get_feature_vector(track):
    return [
        track.energy,
        track.danceability,
        track.valence,
        track.acousticness,
        track.instrumentalness,
        track.speechiness,
        track.tempo / 243.372,
        (track.loudness - (-49.531)) / (4.532 - (-49.531))
    ]

def build_feature_matrix():
    with SessionLocal() as db:
        tracks = db.execute(select(Track)).scalars().all()
        feature_matrix = []
        valid_tracks_id = []
        for track in tracks:
            current_track = get_feature_vector(track)
            if not(None in current_track):
                feature_matrix.append(current_track)
                valid_tracks_id.append(track.track_id)
        return feature_matrix, valid_tracks_id

def best_k_finder(matrix):
    for k in range(3, 11):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        predicted_labels = model.fit_predict(matrix)
        silhouette_val = silhouette_score(matrix, predicted_labels)
        print(k, model.inertia_, silhouette_val)
#best k is 4

model = KMeans(n_clusters=4,
               random_state=42,
               n_init=10)
feature_matrix, valid_ids = build_feature_matrix()
labels = model.fit_predict(feature_matrix)

'''--------------- MODEL/ CLUSTER ANALYSIS -----------------
centroids = model.cluster_centers_
print(centroids)

first_5_per_cluster = {
    cluster: np.where(labels == cluster)[0][:5]
    for cluster in range(model.n_clusters)
}

for cluster, indices in first_5_per_cluster.items():
    print(f"Cluster {cluster} first 5 row indices: {indices}")
    for i in indices:
        print(feature_matrix[i])'''