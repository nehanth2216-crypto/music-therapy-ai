You are a Senior AI Engineer, Machine Learning Engineer, and Full Stack Developer specializing in music recommendation systems.

I have already built a project called "HarmonyRec", an AI-powered Music Therapy Recommendation web application using the following stack:

Backend:
- FastAPI
- Python
- SQLAlchemy
- SQLite/PostgreSQL
- JWT Authentication
- Spotify Web API
- Scikit-learn
- XGBoost
- Random Forest
- Decision Tree
- KNN
- Pandas
- NumPy

Frontend:
- React
- Vite
- Chart.js
- JavaScript

Current Features:
- User Authentication
- Mental Health Survey
- Dashboard
- Mood Journaling
- AI Chat Assistant
- Spotify Track Recommendation
- Listening History
- Favorite Songs
- ML Model Comparison Dashboard

Current Problem:
The recommendation engine is poor.

It mostly recommends generic English songs instead of highly personalized therapeutic music.

The recommendations are mainly based on a simple Spotify genre search instead of true AI-based recommendation.

I want you to completely redesign ONLY the recommendation engine while keeping the rest of the project unchanged.

The new recommendation system should work like a production-level AI application.

Requirements:

1. Use XGBoost as the primary prediction model.

2. Predict Therapy Category instead of only Genre.

Example Therapy Categories:
- Sleep Therapy
- Anxiety Relief
- Stress Relief
- Meditation
- Relaxation
- Focus
- Motivation
- Workout
- Emotional Healing
- Happiness

3. Build a Feature Engineering Pipeline using:

- Mood
- Stress Level
- Anxiety Level
- Sleep Quality
- Activity
- Preferred Language
- Preferred Genres
- Listening History
- Favorite Artists
- Time of Day

4. Improve Spotify search.

Instead of

genre = Pop

search should become

Language + Therapy + Genre

Examples:

"Telugu Relaxing Lo-fi"

"Hindi Meditation"

"Tamil Sleep Music"

"English Focus Instrumental"

"Kannada Devotional"

5. Add support for multiple languages.

Languages should include:

English
Telugu
Hindi
Tamil
Kannada
Malayalam
Punjabi
Marathi
Gujarati
Bengali
Urdu
Japanese
Korean
Chinese
Spanish
French
German
Italian

The language selected by the user must strictly filter recommendations.

6. Use Spotify audio features (or equivalent metadata if audio features are unavailable):

- Energy
- Valence
- Danceability
- Tempo
- Acousticness
- Instrumentalness
- Speechiness

Match songs according to the user's mental health state.

Example:

High Anxiety

↓

Low Energy
Slow Tempo
High Acousticness
Instrumental

Gym

↓

High Energy
High Tempo
High Danceability

Study

↓

Instrumental
Medium Energy
Low Speechiness

7. Build a Recommendation Ranking Engine.

Calculate a recommendation score using:

35% Mood Match

25% Therapy Match

15% Activity Match

10% Language Match

10% Listening History Similarity

5% Popularity

Return only the highest-ranked songs.

8. Add Learning From User Feedback.

Store:

Liked Songs

Skipped Songs

Recently Played

Favorite Genres

Favorite Languages

Favorite Artists

Improve future recommendations using this history.

9. Build a Hybrid Recommendation System.

Pipeline should be:

User Survey

↓

Feature Engineering

↓

XGBoost Prediction

↓

Therapy Category Prediction

↓

Spotify Search

↓

Content-Based Filtering

↓

Listening History Matching

↓

Recommendation Ranking

↓

Top 20 Songs

↓

Save User Feedback

10. Improve Dataset Handling.

If dataset is too small, generate synthetic balanced samples using SMOTE.

Handle class imbalance properly.

Perform feature scaling and label encoding.

11. Refactor the backend into clean modules:

ml/
│
├── feature_engineering.py
├── predictor.py
├── recommender.py
├── spotify_service.py
├── ranking.py
├── feedback.py
├── history.py

12. Keep all existing APIs compatible with the frontend.

Do NOT break any frontend functionality.

13. Optimize for speed.

Use caching where appropriate.

Avoid unnecessary Spotify API calls.

14. Improve recommendation quality rather than simply increasing the number of songs.

15. If any existing recommendation logic is poor, replace it completely with better logic while keeping the UI unchanged.

Output:
- Explain every improvement.
- Provide complete production-ready Python code.
- Provide updated FastAPI endpoints.
- Provide any required database changes.
- Explain how to integrate each file into my existing HarmonyRec project.
- Ensure the final system is modular, scalable, and ready for deployment on Render (backend) and Vercel (frontend).