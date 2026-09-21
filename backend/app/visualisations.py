from sklearn.decomposition import PCA

from app.clustering import feature_matrix, valid_ids


pca = PCA(n_components=2)

coordinates = pca.fit_transform(feature_matrix)

explained_variance = pca.explained_variance_ratio_

def project_profile(profile_vector):
    return pca.transform([profile_vector])[0]