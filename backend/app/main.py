from.database import Base, engine, SessionLocal
from.models import Track
from.schemas import TrackResponse
from fastapi import FastAPI
from sqlalchemy import select

app = FastAPI()

@app.get("/")
def basic_message():
    return {"message": "Resonance API is running"}

@app.get("/tracks", response_model =list[TrackResponse])
def get_tracks():
    statement = select(Track).limit(50)
    with SessionLocal() as db:
        result = db.execute(statement)
        return result.scalars().all()