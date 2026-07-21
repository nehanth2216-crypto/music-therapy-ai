import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, confusion_matrix

# Directories setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, "models"), exist_ok=True)

# Categorical mappings
MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"]
SLEEP_QUALITIES = ["Good", "Fair", "Poor"]
ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation"]
GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"]
PLAYLISTS = ["playlist_1", "playlist_2", "playlist_3", "playlist_4", "playlist_5"]

def generate_synthetic_data(num_samples=5000, random_seed=42):
    np.random.seed(random_seed)
    
    # Generate random features
    age = np.random.randint(15, 75, size=num_samples)
    
    # Probability distribution for moods
    mood = np.random.choice(MOODS, size=num_samples)
    stress = np.random.randint(1, 11, size=num_samples)
    sleep_quality = np.random.choice(SLEEP_QUALITIES, size=num_samples)
    anxiety = np.random.randint(1, 11, size=num_samples)
    activity = np.random.choice(ACTIVITIES, size=num_samples)
    fav_genre = np.random.choice(GENRES, size=num_samples)
    language = np.random.choice(["English", "Spanish", "Hindi", "Other"], p=[0.7, 0.1, 0.1, 0.1], size=num_samples)
    gender = np.random.choice(["Male", "Female", "Other", "Prefer not to say"], p=[0.45, 0.45, 0.05, 0.05], size=num_samples)

    # Determine recommended playlist based on clinical rules
    recommended_playlist = []
    
    for i in range(num_samples):
        # Default fallback
        playlist = "playlist_1"
        
        # Rule 1: High stress, Sleeping activity, Sad mood -> Classical (playlist_2)
        if stress[i] >= 7 and activity[i] == "Sleeping":
            playlist = "playlist_2"
        # Rule 2: High anxiety, Meditation activity -> Nature Sounds (playlist_3)
        elif anxiety[i] >= 7 and activity[i] == "Meditation":
            playlist = "playlist_3"
        # Rule 3: High stress, Relaxation activity, Angry mood -> Instrumental (playlist_4)
        elif stress[i] >= 6 and activity[i] == "Relaxation" and mood[i] == "Angry":
            playlist = "playlist_4"
        # Rule 4: Medium/Low stress, Exercise activity, Tired mood -> Pop (playlist_5)
        elif activity[i] == "Exercise" and (mood[i] == "Tired" or stress[i] <= 5):
            playlist = "playlist_5"
        # Rule 5: Studying activity, Happy mood -> Lofi (playlist_1)
        elif activity[i] == "Studying":
            playlist = "playlist_1"
        # Alternate fallbacks to balance classes
        else:
            if mood[i] == "Sad":
                playlist = "playlist_2"
            elif mood[i] == "Anxiety":
                playlist = "playlist_3"
            elif mood[i] == "Angry":
                playlist = "playlist_4"
            elif mood[i] == "Tired":
                playlist = "playlist_5"
            else:
                playlist = "playlist_1"
                
        recommended_playlist.append(playlist)

    df = pd.DataFrame({
        "Age": age,
        "Gender": gender,
        "Mood": mood,
        "Stress": stress,
        "SleepQuality": sleep_quality,
        "Anxiety": anxiety,
        "FavGenre": fav_genre,
        "Language": language,
        "Activity": activity,
        "RecommendedPlaylist": recommended_playlist
    })
    
    return df

def preprocess_df(df):
    # Encode categorical to index for training
    df_encoded = df.copy()
    
    df_encoded["Mood"] = df_encoded["Mood"].apply(lambda x: MOODS.index(x))
    df_encoded["SleepQuality"] = df_encoded["SleepQuality"].apply(lambda x: SLEEP_QUALITIES.index(x))
    df_encoded["Activity"] = df_encoded["Activity"].apply(lambda x: ACTIVITIES.index(x))
    df_encoded["FavGenre"] = df_encoded["FavGenre"].apply(lambda x: GENRES.index(x))
    
    # Drop irrelevant columns for simplified model inputs
    X = df_encoded[["Age", "Mood", "Stress", "SleepQuality", "Anxiety", "Activity", "FavGenre"]]
    y = df_encoded["RecommendedPlaylist"].apply(lambda x: PLAYLISTS.index(x))
    
    return X, y

def run_pipeline():
    print("Generating synthetic music recommendation dataset...")
    df = generate_synthetic_data(num_samples=6000)
    
    # Save dataset to CSV in the project's dataset directory
    csv_path = os.path.join(DATASET_DIR, "music_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path}")
    
    # Preprocess
    X, y = preprocess_df(df)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # Scale numerical values
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Apply SMOTE to handle minor class imbalances from generated rules
    print("Balancing training sets using SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    
    # Models to train
    models = {
        "Decision Tree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, eval_metric="mlogloss", random_state=42)
    }
    
    metrics_summary = {}
    
    print("\nTraining and evaluating models...")
    for model_name, clf in models.items():
        print(f"Training {model_name}...")
        clf.fit(X_train_res, y_train_res)
        y_pred = clf.predict(X_test_scaled)
        
        # Calculate performance metrics
        report = classification_report(y_test, y_pred, output_dict=True)
        conf_mat = confusion_matrix(y_test, y_pred).tolist()
        acc = np.mean(y_pred == y_test.values)
        
        metrics_summary[model_name] = {
            "accuracy": round(acc, 4),
            "precision": round(report["weighted avg"]["precision"], 4),
            "recall": round(report["weighted avg"]["recall"], 4),
            "f1": round(report["weighted avg"]["f1-score"], 4),
            "confusion_matrix": conf_mat,
            "report": report
        }
        print(f"-> {model_name} validation accuracy: {acc * 100:.2f}%")
        
        # Save champion (using XGBoost or Random Forest based on validation performance)
        if model_name == "XGBoost":
            champion_model = clf
            
    # Save files
    model_save_path = os.path.join(PROJECT_DIR, "models", "recommendation_model.pkl")
    scaler_save_path = os.path.join(PROJECT_DIR, "models", "scaler.pkl")
    metrics_save_path = os.path.join(BASE_DIR, "metrics.json")
    
    with open(model_save_path, "wb") as f:
        pickle.dump(champion_model, f)
    with open(scaler_save_path, "wb") as f:
        pickle.dump(scaler, f)
        
    with open(metrics_save_path, "w") as f:
        json.dump(metrics_summary, f, indent=4)
        
    print(f"\nModel pipeline finished successfully!")
    print(f"Saved model to {model_save_path}")
    print(f"Saved scaler to {scaler_save_path}")
    print(f"Saved validation metrics to {metrics_save_path}")

if __name__ == "__main__":
    run_pipeline()
