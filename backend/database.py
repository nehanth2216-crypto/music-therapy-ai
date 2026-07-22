import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import os

def load_env():
    paths = [".env", "backend/.env", "../.env"]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

load_env()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./harmonyrec.db")

# connect_args={"check_same_thread": False} is only required/supported for SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Resolve postgres:// to postgresql:// if needed for SQLAlchemy
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    fav_genre = Column(String, default="Lo-fi", nullable=True)
    language_pref = Column(String, default="English", nullable=True)
    default_activity = Column(String, default="Relaxation", nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    surveys = relationship("SurveyResponse", back_populates="user")
    journals = relationship("DailyJournal", back_populates="user")
    favorites = relationship("FavoriteTrack", back_populates="user")
    listening_history = relationship("ListeningHistory", back_populates="user")
    playlists = relationship("UserPlaylist", back_populates="user")

class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=True) # Optional
    mood = Column(String, nullable=False) # e.g. Happy, Sad, Anxiety, Angry, Tired
    stress = Column(Integer, nullable=False) # 1-10
    sleep_quality = Column(String, nullable=False) # Good, Fair, Poor
    anxiety = Column(Integer, nullable=False) # 1-10
    fav_genre = Column(String, nullable=False) # Favorite genre
    language_pref = Column(String, nullable=False) # Language preference
    activity = Column(String, nullable=False) # Studying, Sleeping, Meditation, Exercise, Relaxation
    result_playlist = Column(String, nullable=False) # Predicted playlist type (e.g. playlist_1, etc.)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="surveys")
    recommendation = relationship("Recommendation", back_populates="survey", uselist=False)

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)
    genre = Column(String, nullable=False) # Recommended genre/playlist style
    tracks = Column(String, nullable=False) # JSON-serialized list of tracks
    rating = Column(Integer, nullable=True) # User rating (1-5 stars)
    helped = Column(Boolean, nullable=True) # Did this music help? (True/False)
    
    survey = relationship("SurveyResponse", back_populates="recommendation")

class DailyJournal(Base):
    __tablename__ = "daily_journals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood = Column(String, nullable=False)
    stress = Column(Integer, nullable=False)
    journal_text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="journals")

class FavoriteTrack(Base):
    __tablename__ = "favorite_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    album_image = Column(String, nullable=True)
    play_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="favorites")

class ListeningHistory(Base):
    __tablename__ = "listening_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    album_image = Column(String, nullable=True)
    play_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)
    played_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="listening_history")

class UserPlaylist(Base):
    __tablename__ = "user_playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("user_playlists.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    album_image = Column(String, nullable=True)
    play_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    playlist = relationship("UserPlaylist", back_populates="tracks")

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight schema migration for existing SQLite/Postgres tables
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        with engine.connect() as conn:
            if "full_name" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
            if "fav_genre" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN fav_genre VARCHAR DEFAULT 'Lo-fi'"))
            if "language_pref" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN language_pref VARCHAR DEFAULT 'English'"))
            if "default_activity" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN default_activity VARCHAR DEFAULT 'Relaxation'"))
            if "reset_token" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR"))
            if "reset_token_expires" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP"))
            conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
