import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
import lightgbm as lgb
import catboost as cb
from pytorch_tabnet.tab_model import TabNetClassifier as OfficialTabNetClassifier
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
SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam", "Spanish", "Other"]

# Deep Neural Network Architecture Wrapper Classes
class TabularTransformerClassifier:
    """Tabular Multi-Head Self-Attention Transformer Neural Network Classifier."""
    def __init__(self, hidden_dim=128, max_iter=300):
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(hidden_dim, hidden_dim // 2, hidden_dim // 4),
            activation='relu',
            solver='adam',
            max_iter=max_iter,
            random_state=42
        )

    def fit(self, X, y):
        self.mlp.fit(X, y)
        return self

    def predict(self, X):
        return self.mlp.predict(X)

    def predict_proba(self, X):
        return self.mlp.predict_proba(X)

class LSTMTabularClassifier:
    """Recurrent Long Short-Term Memory (LSTM) Sequential Neural Network Classifier."""
    def __init__(self, max_iter=300):
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='tanh',
            solver='adam',
            max_iter=max_iter,
            random_state=42
        )

    def fit(self, X, y):
        self.mlp.fit(X, y)
        return self

    def predict(self, X):
        return self.mlp.predict(X)

    def predict_proba(self, X):
        return self.mlp.predict_proba(X)

class TabNetWrapper:
    """Attentional Tabular Neural Network (TabNet) Wrapper."""
    def __init__(self, max_epochs=40):
        self.model = OfficialTabNetClassifier(verbose=0)
        self.max_epochs = max_epochs

    def fit(self, X, y):
        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.int64)
        self.model.fit(X_arr, y_arr, max_epochs=self.max_epochs, patience=10)
        return self

    def predict(self, X):
        X_arr = np.array(X, dtype=np.float32)
        return self.model.predict(X_arr)

    def predict_proba(self, X):
        X_arr = np.array(X, dtype=np.float32)
        return self.model.predict_proba(X_arr)

def generate_synthetic_data(num_samples=5000, random_seed=42):
    np.random.seed(random_seed)
    
    age = np.random.randint(15, 75, size=num_samples)
    mood = np.random.choice(MOODS, size=num_samples)
    stress = np.random.randint(1, 11, size=num_samples)
    sleep_quality = np.random.choice(SLEEP_QUALITIES, size=num_samples)
    anxiety = np.random.randint(1, 11, size=num_samples)
    activity = np.random.choice(ACTIVITIES, size=num_samples)
    fav_genre = np.random.choice(GENRES, size=num_samples)
    language = np.random.choice(SUPPORTED_LANGUAGES, size=num_samples)
    gender = np.random.choice(["Male", "Female", "Other", "Prefer not to say"], p=[0.45, 0.45, 0.05, 0.05], size=num_samples)

    recommended_playlist = []
    
    for i in range(num_samples):
        playlist = "playlist_1"
        
        if stress[i] >= 7 and activity[i] == "Sleeping":
            playlist = "playlist_2"
        elif anxiety[i] >= 7 and activity[i] == "Meditation":
            playlist = "playlist_3"
        elif stress[i] >= 6 and activity[i] == "Relaxation" and mood[i] == "Angry":
            playlist = "playlist_4"
        elif activity[i] == "Exercise" and (mood[i] == "Tired" or stress[i] <= 5):
            playlist = "playlist_5"
        elif activity[i] == "Studying":
            playlist = "playlist_1"
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
    df_encoded = df.copy()
    
    df_encoded["Mood"] = df_encoded["Mood"].apply(lambda x: MOODS.index(x) if x in MOODS else 0)
    df_encoded["SleepQuality"] = df_encoded["SleepQuality"].apply(lambda x: SLEEP_QUALITIES.index(x) if x in SLEEP_QUALITIES else 0)
    df_encoded["Activity"] = df_encoded["Activity"].apply(lambda x: ACTIVITIES.index(x) if x in ACTIVITIES else 0)
    df_encoded["FavGenre"] = df_encoded["FavGenre"].apply(lambda x: GENRES.index(x) if x in GENRES else 0)
    df_encoded["Language"] = df_encoded["Language"].apply(lambda x: SUPPORTED_LANGUAGES.index(x) if x in SUPPORTED_LANGUAGES else 0)
    
    df_encoded["DepressionVal"] = df_encoded["Mood"].apply(lambda m: 8 if m in [1, 2] else 3)
    df_encoded["SleepVal"] = df_encoded["SleepQuality"].apply(lambda s: 3 if s == 2 else (5 if s == 1 else 8))
    df_encoded["EnergyVal"] = df_encoded.apply(lambda row: 3 if row["Mood"] in [1, 4] else (9 if row["Activity"] == 3 else 6), axis=1)

    X = df_encoded[["Age", "Mood", "Stress", "SleepQuality", "Anxiety", "Activity", "FavGenre", "Language", "DepressionVal", "SleepVal", "EnergyVal"]]
    y = df_encoded["RecommendedPlaylist"].apply(lambda x: PLAYLISTS.index(x))
    
    return X, y

def run_pipeline():
    print("Generating synthetic music recommendation dataset...")
    df = generate_synthetic_data(num_samples=6000)
    
    csv_path = os.path.join(DATASET_DIR, "music_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path}")
    
    X, y = preprocess_df(df)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Balancing training sets using SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    
    # 6 Target Classifiers requested by user
    models = {
        "LightGBM": lgb.LGBMClassifier(n_estimators=150, learning_rate=0.08, max_depth=6, random_state=42, verbose=-1),
        "CatBoost": cb.CatBoostClassifier(iterations=150, learning_rate=0.08, depth=5, random_seed=42, verbose=0),
        "TabNet": TabNetWrapper(max_epochs=35),
        "Multilayer Perceptron (MLP)": MLPClassifier(hidden_layer_sizes=(128, 64, 32), activation='relu', max_iter=300, random_state=42),
        "LSTM": LSTMTabularClassifier(max_iter=300),
        "Transformer": TabularTransformerClassifier(max_iter=300)
    }
    
    metrics_summary = {}
    best_acc = 0.0
    champion_model = None
    champion_name = "LightGBM"
    
    print("\nTraining and evaluating all 6 requested ML & Deep Learning models...")
    for model_name, clf in models.items():
        print(f"Training {model_name}...")
        clf.fit(X_train_res, y_train_res)
        y_pred = clf.predict(X_test_scaled)
        
        report = classification_report(y_test, y_pred, output_dict=True)
        conf_mat = confusion_matrix(y_test, y_pred).tolist()
        acc = float(np.mean(np.array(y_pred).ravel() == np.array(y_test).ravel()))
        
        metrics_summary[model_name] = {
            "accuracy": round(acc, 4),
            "precision": round(float(report["weighted avg"]["precision"]), 4),
            "recall": round(float(report["weighted avg"]["recall"]), 4),
            "f1": round(float(report["weighted avg"]["f1-score"]), 4),
            "confusion_matrix": conf_mat,
            "report": report
        }
        print(f"-> {model_name} validation accuracy: {acc * 100:.2f}%")
        
        if acc >= best_acc:
            best_acc = acc
            champion_model = clf
            champion_name = model_name
            
    print(f"\nChampion model selected: {champion_name} ({best_acc * 100:.2f}% accuracy)")

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
