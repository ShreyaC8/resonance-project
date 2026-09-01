import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base
from app.main import app, get_db
from app.models import Track


TEST_DATABASE_URL = "sqlite:///./test_resonance.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    db.add_all([
        Track(
            track_id="seed-1",
            track_name="Happy Song",
            artists="Artist A",
            track_genre="pop",
            popularity=70,
            energy=0.8,
            danceability=0.7,
            valence=0.8,
        ),
        Track(
            track_id="seed-2",
            track_name="Dance Song",
            artists="Artist B",
            track_genre="pop",
            popularity=80,
            energy=0.9,
            danceability=0.9,
            valence=0.7,
        ),
        Track(
            track_id="similar-1",
            track_name="Similar Song",
            artists="Artist C",
            track_genre="pop",
            popularity=75,
            energy=0.85,
            danceability=0.8,
            valence=0.75,
        ),
        Track(
            track_id="different-1",
            track_name="Different Song",
            artists="Artist D",
            track_genre="metal",
            popularity=40,
            energy=0.1,
            danceability=0.2,
            valence=0.1,
        ),
    ])

    db.commit()
    db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)