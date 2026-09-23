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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    surveys = relationship("SurveyResponse", back_populates="user")
    journals = relationship("DailyJournal", back_populates="user")
    favorites = relationship("FavoriteTrack", back_populates="user")
    listening_history = relationship("ListeningHistory", back_populates="user")
    playlists = relationship("UserPlaylist", back_populates="user")
    track_feedbacks = relationship("TrackFeedback", back_populates="user")

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
    energy = Column(String, default="Medium", nullable=True) # Low, Medium, High
    result_playlist = Column(String, nullable=False) # Predicted playlist type (e.g. playlist_1, etc.)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
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
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
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
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
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
    language = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    mood = Column(String, nullable=True)
    activity = Column(String, nullable=True)
    energy = Column(String, nullable=True)
    recommendation_score = Column(Float, nullable=True)
    played_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    
    user = relationship("User", back_populates="listening_history")

class UserPlaylist(Base):
    __tablename__ = "user_playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    
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
    added_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    playlist = relationship("UserPlaylist", back_populates="tracks")

class TrackFeedback(Base):
    __tablename__ = "track_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    action = Column(String, nullable=False) # 'like', 'skip', 'play'
    therapy_category = Column(String, nullable=True)
    language = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    
    user = relationship("User", back_populates="track_feedbacks")

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight schema migration for existing SQLite/Postgres tables
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.connect() as conn:
        if "users" in table_names:
            columns = [c["name"] for c in inspector.get_columns("users")]
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
        
        if "survey_responses" in table_names:
            sr_cols = [c["name"] for c in inspector.get_columns("survey_responses")]
            if "hours_per_day" in sr_cols:
                # Migrate from legacy schema with obsolete NOT NULL constraints
                conn.execute(text("""
                    CREATE TABLE survey_responses_v2 (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        age INTEGER NOT NULL,
                        gender VARCHAR,
                        mood VARCHAR NOT NULL,
                        stress INTEGER NOT NULL,
                        sleep_quality VARCHAR NOT NULL,
                        anxiety INTEGER NOT NULL,
                        fav_genre VARCHAR NOT NULL,
                        language_pref VARCHAR NOT NULL,
                        activity VARCHAR NOT NULL,
                        energy VARCHAR DEFAULT 'Medium',
                        result_playlist VARCHAR NOT NULL,
                        timestamp DATETIME
                    )
                """))
                conn.execute(text("""
                    INSERT INTO survey_responses_v2 (id, user_id, age, gender, mood, stress, sleep_quality, anxiety, fav_genre, language_pref, activity, energy, result_playlist, timestamp)
                    SELECT id, user_id, age, COALESCE(gender, 'Not Specified'), COALESCE(mood, 'Calm'), COALESCE(stress, 5), COALESCE(sleep_quality, 'Fair'), anxiety, fav_genre, COALESCE(language_pref, 'English'), COALESCE(activity, 'Relaxation'), COALESCE(energy, 'Medium'), COALESCE(result_playlist, 'Calming'), timestamp
                    FROM survey_responses
                """))
                conn.execute(text("DROP TABLE survey_responses"))
                conn.execute(text("ALTER TABLE survey_responses_v2 RENAME TO survey_responses"))
            else:
                if "gender" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN gender VARCHAR"))
                if "energy" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN energy VARCHAR DEFAULT 'Medium'"))
                if "mood" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN mood VARCHAR"))
                if "stress" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN stress INTEGER"))
                if "sleep_quality" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN sleep_quality VARCHAR"))
                if "language_pref" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN language_pref VARCHAR"))
                if "activity" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN activity VARCHAR"))
                if "result_playlist" not in sr_cols:
                    conn.execute(text("ALTER TABLE survey_responses ADD COLUMN result_playlist VARCHAR"))
                
        if "recommendations" in table_names:
            rec_cols = [c["name"] for c in inspector.get_columns("recommendations")]
            if "rating" not in rec_cols:
                conn.execute(text("ALTER TABLE recommendations ADD COLUMN rating INTEGER"))
            if "helped" not in rec_cols:
                conn.execute(text("ALTER TABLE recommendations ADD COLUMN helped BOOLEAN"))

        if "listening_history" in table_names:
            lh_cols = [c["name"] for c in inspector.get_columns("listening_history")]
            if "language" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN language VARCHAR"))
            if "genre" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN genre VARCHAR"))
            if "mood" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN mood VARCHAR"))
            if "activity" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN activity VARCHAR"))
            if "energy" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN energy VARCHAR"))
            if "recommendation_score" not in lh_cols:
                conn.execute(text("ALTER TABLE listening_history ADD COLUMN recommendation_score FLOAT"))
        
        conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
