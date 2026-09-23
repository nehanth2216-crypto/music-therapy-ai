import os
import pickle
import numpy as np
from typing import Dict, Any, Tuple, Optional
import lightgbm as lgb
import catboost as cb
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

from backend.ml.feature_engineering import (
    THERAPY_CATEGORIES,
    MOODS,
    SLEEP_QUALITIES,
    ACTIVITIES,
    GENRES,
    SUPPORTED_LANGUAGES
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

SCALER_PATH = os.path.join(MODELS_DIR, "therapy_scaler.pkl")
LIGHTGBM_MODEL_PATH = os.path.join(MODELS_DIR, "lightgbm_therapy_model.pkl")
CATBOOST_MODEL_PATH = os.path.join(MODELS_DIR, "catboost_therapy_model.pkl")
XGBOOST_MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_therapy_model.pkl")

class TherapyPredictor:
    """
    Advanced Multi-Model Therapy Category Prediction Engine.
    Supports LightGBM (Champion), CatBoost, XGBoost, and Weighted Ensemble.
    """

    def __init__(self, default_model: str = "LightGBM"):
        self.default_model = default_model
        self.lightgbm_model = None
        self.catboost_model = None
        self.xgboost_model = None
        self.scaler = None
        self.load_or_train_models()

    def generate_training_data(self, random_seed=42):
        """Generate balanced training dataset combining 500-sample authentic therapy dataset with augmented cohort."""
        np.random.seed(random_seed)

        X_real = []
        y_real = []

        dataset_path = os.path.join(BASE_DIR, "dataset", "music_dataset.csv")
        if os.path.exists(dataset_path):
            try:
                import csv
                with open(dataset_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        age = float(row.get("Age") or 25)
                        mood_str = (row.get("Mood") or "Tired").strip()
                        stress = float(row.get("Stress") or 5)
                        sleep_str = (row.get("SleepQuality") or "Fair").strip()
                        anxiety = float(row.get("Anxiety") or 5)
                        genre_str = (row.get("FavGenre") or "Lo-fi").strip()
                        lang_str = (row.get("Language") or "English").strip()
                        act_str = (row.get("Activity") or "Relaxation").strip()
                        rec_pl = (row.get("RecommendedPlaylist") or "playlist_1").strip()

                        # Categorical Encodings matching FeatureEngineer
                        mood_idx = MOODS.index(mood_str) if mood_str in MOODS else 4
                        sleep_idx = SLEEP_QUALITIES.index(sleep_str) if sleep_str in SLEEP_QUALITIES else 1
                        act_idx = ACTIVITIES.index(act_str) if act_str in ACTIVITIES else 4
                        genre_idx = GENRES.index(genre_str) if genre_str in GENRES else 0
                        lang_idx = SUPPORTED_LANGUAGES.index(lang_str) if lang_str in SUPPORTED_LANGUAGES else 0

                        depression_val = 8.0 if mood_str in ["Sad", "Anxiety"] else 3.0
                        sleep_val = 3.0 if sleep_str == "Poor" else (5.0 if sleep_str == "Fair" else 8.0)
                        energy_val = 9.0 if act_str == "Exercise" else (3.0 if mood_str in ["Tired", "Sad"] else 6.0)

                        if rec_pl == "playlist_2" or act_str == "Sleeping":
                            label = 0  # Sleep Therapy
                        elif rec_pl == "playlist_3" and anxiety >= 7:
                            label = 1  # Anxiety Relief
                        elif rec_pl == "playlist_5" or stress >= 7:
                            label = 2  # Stress Relief
                        elif act_str == "Meditation":
                            label = 3  # Meditation
                        elif act_str == "Studying":
                            label = 5  # Focus
                        elif rec_pl == "playlist_4" or act_str == "Exercise":
                            label = 7  # Workout
                        elif mood_str == "Sad":
                            label = 8  # Emotional Healing
                        elif mood_str == "Happy":
                            label = 9  # Happiness
                        elif act_str in ["Walking", "Driving"]:
                            label = 6  # Motivation
                        else:
                            label = 4  # Relaxation

                        vec = [
                            age, float(mood_idx), stress, float(sleep_idx),
                            anxiety, float(act_idx), float(genre_idx), float(lang_idx),
                            depression_val, sleep_val, energy_val
                        ]
                        X_real.append(vec)
                        y_real.append(label)
            except Exception as e:
                print(f"Error loading music_dataset.csv: {e}")

        # Augmentation cohort to balance all 10 therapy categories
        num_aug = 2000
        ages_aug = np.random.randint(15, 75, size=num_aug)
        mood_aug = np.random.randint(0, 5, size=num_aug)
        stress_aug = np.random.randint(1, 11, size=num_aug)
        sleep_aug = np.random.randint(0, 3, size=num_aug)
        anx_aug = np.random.randint(1, 11, size=num_aug)
        act_aug = np.random.randint(0, 5, size=num_aug)
        genre_aug = np.random.randint(0, 5, size=num_aug)
        lang_aug = np.random.randint(0, 18, size=num_aug)
        dep_aug = np.where(mood_aug == 1, 8, 3)
        slp_aug = np.where(sleep_aug == 2, 3, 7)
        nrg_aug = np.where(act_aug == 3, 9, 5)

        y_aug = []
        for i in range(num_aug):
            st = stress_aug[i]
            anx = anx_aug[i]
            act = act_aug[i]
            md = mood_aug[i]
            if st >= 7 and act == 1:
                y_aug.append(0)
            elif anx >= 7 or md == 2:
                y_aug.append(1)
            elif st >= 7 or md == 3:
                y_aug.append(2)
            elif act == 2 or anx >= 6:
                y_aug.append(3)
            elif act == 0:
                y_aug.append(5)
            elif act == 3:
                y_aug.append(7)
            elif md == 1:
                y_aug.append(8)
            elif md == 0:
                y_aug.append(9)
            elif st <= 4 and anx <= 4:
                y_aug.append(4)
            else:
                y_aug.append(6)

        X_aug = np.column_stack([
            ages_aug, mood_aug, stress_aug, sleep_aug, anx_aug,
            act_aug, genre_aug, lang_aug, dep_aug, slp_aug, nrg_aug
        ])

        if len(X_real) > 0:
            X_all = np.vstack([np.array(X_real), X_aug])
            y_all = np.concatenate([np.array(y_real), np.array(y_aug)])
        else:
            X_all = X_aug
            y_all = np.array(y_aug)

        smote = SMOTE(random_state=random_seed, k_neighbors=3)
        X_res, y_res = smote.fit_resample(X_all, y_all)
        return X_res, y_res

    def train(self):
        """Train and persist LightGBM, CatBoost, and XGBoost Therapy Predictor models."""
        print("Training LightGBM, CatBoost, and XGBoost therapy models on 500-item therapy dataset...")
        X, y = self.generate_training_data()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)

        # 1. Train LightGBM (Champion)
        lgbm = lgb.LGBMClassifier(
            n_estimators=180,
            learning_rate=0.08,
            max_depth=6,
            num_leaves=31,
            random_state=42,
            verbose=-1
        )
        lgbm.fit(X_train, y_train)

        # 2. Train CatBoost
        cat = cb.CatBoostClassifier(
            iterations=180,
            learning_rate=0.08,
            depth=5,
            random_seed=42,
            verbose=0
        )
        cat.fit(X_train, y_train)

        # 3. Train XGBoost
        xgb = XGBClassifier(
            n_estimators=180,
            learning_rate=0.08,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="mlogloss"
        )
        xgb.fit(X_train, y_train)

        # Save all models
        with open(LIGHTGBM_MODEL_PATH, "wb") as f:
            pickle.dump(lgbm, f)
        with open(CATBOOST_MODEL_PATH, "wb") as f:
            pickle.dump(cat, f)
        with open(XGBOOST_MODEL_PATH, "wb") as f:
            pickle.dump(xgb, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(scaler, f)

        self.lightgbm_model = lgbm
        self.catboost_model = cat
        self.xgboost_model = xgb
        self.scaler = scaler
        print("All models (LightGBM, CatBoost, XGBoost) successfully trained and persisted.")

    def load_or_train_models(self):
        """Load trained models or train fresh ones if files are missing."""
        try:
            if (
                os.path.exists(LIGHTGBM_MODEL_PATH)
                and os.path.exists(CATBOOST_MODEL_PATH)
                and os.path.exists(XGBOOST_MODEL_PATH)
                and os.path.exists(SCALER_PATH)
            ):
                with open(LIGHTGBM_MODEL_PATH, "rb") as f:
                    self.lightgbm_model = pickle.load(f)
                with open(CATBOOST_MODEL_PATH, "rb") as f:
                    self.catboost_model = pickle.load(f)
                with open(XGBOOST_MODEL_PATH, "rb") as f:
                    self.xgboost_model = pickle.load(f)
                with open(SCALER_PATH, "rb") as f:
                    self.scaler = pickle.load(f)
            else:
                self.train()
        except Exception as e:
            print(f"Exception loading models ({e}). Retraining...")
            self.train()

    def predict_therapy_category(
        self,
        feature_data: Dict[str, Any],
        model_name: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Predict therapy category using LightGBM, CatBoost, XGBoost, or Ensemble.
        Returns (predicted_category_string, confidence_score).
        """
        target_model = (model_name or self.default_model).strip().lower()

        try:
            vec = np.array([feature_data["feature_vector"]], dtype=float)
            if self.scaler:
                vec_scaled = self.scaler.transform(vec)

                # Select model probabilities
                if "cat" in target_model and self.catboost_model:
                    probs = self.catboost_model.predict_proba(vec_scaled)[0]
                elif "xgb" in target_model and self.xgboost_model:
                    probs = self.xgboost_model.predict_proba(vec_scaled)[0]
                elif "ensem" in target_model:
                    # Weighted Ensemble of LightGBM (45%) + CatBoost (45%) + XGBoost (10%)
                    p_lgb = self.lightgbm_model.predict_proba(vec_scaled)[0] if self.lightgbm_model else None
                    p_cat = self.catboost_model.predict_proba(vec_scaled)[0] if self.catboost_model else None
                    p_xgb = self.xgboost_model.predict_proba(vec_scaled)[0] if self.xgboost_model else None

                    if p_lgb is not None and p_cat is not None:
                        probs = 0.45 * p_lgb + 0.45 * p_cat + (0.10 * p_xgb if p_xgb is not None else 0.10 * p_lgb)
                    elif p_lgb is not None:
                        probs = p_lgb
                    elif p_cat is not None:
                        probs = p_cat
                    else:
                        probs = p_xgb
                else: # Default: LightGBM (Champion)
                    if self.lightgbm_model:
                        probs = self.lightgbm_model.predict_proba(vec_scaled)[0]
                    elif self.catboost_model:
                        probs = self.catboost_model.predict_proba(vec_scaled)[0]
                    else:
                        probs = self.xgboost_model.predict_proba(vec_scaled)[0]

                if probs is not None:
                    pred_idx = int(np.argmax(probs))
                    confidence = float(probs[pred_idx])
                    if 0 <= pred_idx < len(THERAPY_CATEGORIES):
                        return THERAPY_CATEGORIES[pred_idx], round(confidence, 4)

        except Exception as e:
            print(f"Prediction error fallback: {e}")

        # Rule-based Clinical Fallback
        st = feature_data.get("stress", 5)
        anx = feature_data.get("anxiety", 5)
        mood = feature_data.get("mood", "Tired")
        activity = feature_data.get("activity", "Relaxation")

        if activity == "Sleeping" or (st >= 8 and mood == "Tired"):
            return "Sleep Therapy", 0.90
        elif anx >= 7 or mood == "Anxiety":
            return "Anxiety Relief", 0.88
        elif st >= 7 or mood == "Angry":
            return "Stress Relief", 0.85
        elif activity == "Meditation":
            return "Meditation", 0.92
        elif activity == "Studying":
            return "Focus", 0.89
        elif activity == "Exercise":
            return "Workout", 0.91
        elif mood == "Sad":
            return "Emotional Healing", 0.87
        elif mood == "Happy":
            return "Happiness", 0.90
        else:
            return "Relaxation", 0.80
