from sqlalchemy.orm import Session
from app.models import UserBehaviorProfile, UserNetworkStats
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import numpy as np
import joblib
import os

MODEL_PATH = "app/model/joint_model.pkl"

def get_recent_network_features(db: Session, user_id: str, window_mins: int = 10):
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_mins)

    stats = db.query(UserNetworkStats).filter(
        UserNetworkStats.user_id == user_id,
        UserNetworkStats.timestamp >= window_start
    ).all()

    if not stats:
        return [0, 0, 0]

    total_dns = sum(s.dns_lookups for s in stats)
    total_bandwidth = sum(s.total_bandwidth_mb for s in stats)
    avg_packet_size = sum(s.avg_packet_size for s in stats) / len(stats)

    return [total_dns, total_bandwidth, avg_packet_size]

def get_combined_features(db: Session, user_id: str):
    b = db.query(UserBehaviorProfile).filter_by(user_id=user_id).first()
    if not b:
        return None
    net = get_recent_network_features(db, user_id)
    return [
        b.avg_login_hour or 0,
        b.total_time_spent or 0,
        b.avg_session_duration or 0,
        b.total_uploads or 0,
        *net
    ]

def train_joint_anomaly_model(db: Session):
    users = db.query(UserBehaviorProfile).all()
    X = [get_combined_features(db, u.user_id) for u in users if get_combined_features(db, u.user_id)]
    if not X:
        raise ValueError("❌ No valid data to train on.")
    
    model = IsolationForest(contamination=0.1)
    model.fit(X)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Trained and saved model on {len(X)} users.")

def load_joint_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not trained yet.")
    return joblib.load(MODEL_PATH)

def model_needs_retraining(db: Session) -> bool:
    """Determine if the number of users has changed since last training."""
    meta_path = MODEL_PATH.replace(".pkl", ".meta")
    current_count = db.query(UserBehaviorProfile).count()
    
    if not os.path.exists(meta_path):
        return True

    with open(meta_path, "r") as f:
        last_count = int(f.read().strip())

    return current_count != last_count

def save_model_metadata(db: Session):
    meta_path = MODEL_PATH.replace(".pkl", ".meta")
    count = db.query(UserBehaviorProfile).count()
    with open(meta_path, "w") as f:
        f.write(str(count))

def compute_joint_anomaly_score(db: Session, user_id: str):
    if model_needs_retraining(db):
        print("🔁 Retraining model due to user count change...")
        train_joint_anomaly_model(db)
        save_model_metadata(db)

    model = load_joint_model()
    vec = get_combined_features(db, user_id)
    if not vec:
        return None

    score = model.decision_function([vec])[0]
    prediction = model.predict([vec])[0]
    return {
        "user_id": user_id,
        "joint_anomaly_score": round(-score, 4),
        "is_anomalous": prediction == -1
    }
