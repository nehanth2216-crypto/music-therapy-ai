import os
import pickle
import numpy as np
from typing import Dict, Any, Tuple
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

from backend.ml.feature_engineering import THERAPY_CATEGORIES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_therapy_model.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "therapy_scaler.pkl")

class TherapyPredictor:
    """XGBoost-based Therapy Category Prediction Model."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.load_or_train_model()

    def generate_synthetic_training_data(self, num_samples=3000, random_seed=42):
        """Generate balanced synthetic training dataset for XGBoost Therapy Category prediction."""
        np.random.seed(random_seed)
        
        ages = np.random.randint(15, 75, size=num_samples)
        mood_idxs = np.random.randint(0, 5, size=num_samples)
        stresses = np.random.randint(1, 11, size=num_samples)
        sleep_idxs = np.random.randint(0, 3, size=num_samples)
        anxieties = np.random.randint(1, 11, size=num_samples)
        activity_idxs = np.random.randint(0, 5, size=num_samples)
        genre_idxs = np.random.randint(0, 5, size=num_samples)
        lang_idxs = np.random.randint(0, 18, size=num_samples)
        
        depressions = np.where(mood_idxs == 1, np.random.randint(7, 11, size=num_samples), np.random.randint(1, 6, size=num_samples))
        sleep_vals = np.where(sleep_idxs == 2, np.random.randint(1, 4, size=num_samples), np.random.randint(5, 10, size=num_samples))
        energy_vals = np.where(activity_idxs == 3, np.random.randint(8, 11, size=num_samples), np.random.randint(2, 7, size=num_samples))

        labels = []
        for i in range(num_samples):
            st = stresses[i]
            anx = anxieties[i]
            act = activity_idxs[i]
            md = mood_idxs[i]
            slp = sleep_idxs[i]

            if st >= 7 and act == 1: # Sleeping activity -> Sleep Therapy
                labels.append(0) # Sleep Therapy
            elif anx >= 7 or md == 2: # Anxiety -> Anxiety Relief
                labels.append(1) # Anxiety Relief
            elif st >= 7 or md == 3: # Stress / Angry -> Stress Relief
                labels.append(2) # Stress Relief
            elif act == 2 or anx >= 6: # Meditation -> Meditation
                labels.append(3) # Meditation
            elif act == 0: # Studying -> Focus
                labels.append(5) # Focus
            elif act == 3: # Workout / Exercise -> Workout
                labels.append(7) # Workout
            elif md == 1: # Sad -> Emotional Healing
                labels.append(8) # Emotional Healing
            elif md == 0: # Happy -> Happiness
                labels.append(9) # Happiness
            elif st <= 4 and anx <= 4:
                labels.append(4) # Relaxation
            else:
                labels.append(6) # Motivation

        X = np.column_stack([
            ages, mood_idxs, stresses, sleep_idxs, anxieties,
            activity_idxs, genre_idxs, lang_idxs, depressions, sleep_vals, energy_vals
        ])
        y = np.array(labels)
        
        # Apply SMOTE to handle class imbalance
        smote = SMOTE(random_state=random_seed, k_neighbors=3)
        X_res, y_res = smote.fit_resample(X, y)
        return X_res, y_res

    def train(self):
        """Train and persist XGBoost Therapy Predictor model."""
        X, y = self.generate_synthetic_training_data()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        model = XGBClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="mlogloss"
        )
        model.fit(X_train, y_train)

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(scaler, f)

        self.model = model
        self.scaler = scaler

    def load_or_train_model(self):
        """Load trained XGBoost model or train a fresh one."""
        try:
            if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(SCALER_PATH, "rb") as f:
                    self.scaler = pickle.load(f)
            else:
                self.train()
        except Exception as e:
            print(f"Warning: Exception loading XGBoost Therapy model ({e}). Retraining...")
            self.train()

    def predict_therapy_category(self, feature_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Predict therapy category (e.g. 'Sleep Therapy', 'Anxiety Relief', etc.)
        Returns (predicted_category_string, confidence_score).
        """
        try:
            vec = np.array([feature_data["feature_vector"]], dtype=float)
            if self.scaler and self.model:
                vec_scaled = self.scaler.transform(vec)
                probs = self.model.predict_proba(vec_scaled)[0]
                pred_idx = int(np.argmax(probs))
                confidence = float(probs[pred_idx])
                if 0 <= pred_idx < len(THERAPY_CATEGORIES):
                    return THERAPY_CATEGORIES[pred_idx], confidence
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
