def test_recommendation_returns_results(client):
    response = client.post(
        "/recommend",
        json={
            "tracks": [
                {
                    "track_id": "seed-1",
                    "track_name": "Happy Song",
                    "artists": "Artist A"
                }
            ],
            "limit": 10
        }
    )

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_recommendation_excludes_seed_tracks(client):
    response = client.post(
        "/recommend",
        json={
            "tracks": [
                {
                    "track_id": "seed-1",
                    "track_name": "Happy Song",
                    "artists": "Artist A"
                }
            ],
            "limit": 10
        }
    )

    results = response.json()
    result_ids = [track["track_id"] for track in results]

    assert "seed-1" not in result_ids


def test_recommendation_is_sorted(client):
    response = client.post(
        "/recommend",
        json={
            "tracks": [
                {
                    "track_id": "seed-1",
                    "track_name": "Happy Song",
                    "artists": "Artist A"
                }
            ],
            "limit": 10
        }
    )

    scores = [track["score"] for track in response.json()]

    assert scores == sorted(scores, reverse=True)


def test_invalid_track_id_returns_404(client):
    response = client.post(
        "/recommend",
        json={
            "tracks": [
                {
                    "track_id": "does-not-exist",
                    "track_name": "Fake Song",
                    "artists": "Fake Artist"
                }
            ],
            "limit": 10
        }
    )

    assert response.status_code == 404


def test_empty_track_ids_returns_422(client):
    response = client.post(
        "/recommend",
        json={
            "tracks": [],
            "limit": 10
        }
    )

    assert response.status_code == 422