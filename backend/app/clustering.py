import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.mixture import GaussianMixture
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
            if not (None in current_track):
                feature_matrix.append(current_track)
                valid_tracks_id.append(track.track_id)
        return feature_matrix, valid_tracks_id

def best_k_finder(matrix):
    """Use BIC to pick the number of GMM components (lower BIC = better tradeoff
    between fit and model complexity). Silhouette score is also printed using
    each model's hard cluster assignment, for comparison against the old
    KMeans-based selection."""
    for k in range(2, 11):
        model = GaussianMixture(n_components=k, random_state=42, n_init=5)
        model.fit(matrix)
        predicted_labels = model.predict(matrix)
        bic_val = model.bic(np.array(matrix))
        silhouette_val = silhouette_score(matrix, predicted_labels)
        print(k, "BIC:", bic_val, "silhouette:", silhouette_val)
#k=3 seems most appropriate

feature_matrix, valid_ids = build_feature_matrix()

gmm_model = GaussianMixture(
    n_components=3,
    random_state=42,
    n_init=5
)
gmm_model.fit(feature_matrix)

#Hard labels (e.g. for the /taste-map visualization endpoint)
labels = gmm_model.predict(feature_matrix)

#Soft membership: probability of each track belonging to each component.
#For a graded, non-hard-boundary cluster filter.
cluster_probs = gmm_model.predict_proba(feature_matrix)

'''--------------- MODEL / CLUSTER ANALYSIS -----------------
means = gmm_model.means_
print(means)

first_5_per_cluster = {
    cluster: np.where(labels == cluster)[0][:5]
    for cluster in range(gmm_model.n_components)
}

for cluster, indices in first_5_per_cluster.items():
    print(f"Cluster {cluster} first 5 row indices: {indices}")
    for i in indices:
        print(feature_matrix[i])
        print("  membership probs:", cluster_probs[i])
'''