# train_model.py
from app.database import SessionLocal
from app.services.joint_model import train_joint_anomaly_model
import os

db = SessionLocal()

print("🔁 Training joint anomaly model...")
try:
    train_joint_anomaly_model(db)
except Exception as e:
    print(f"❌ Error during training: {e}")

model_path = "app/model/joint_model.pkl"
if os.path.exists(model_path):
    print(f"✅ File successfully saved: {model_path}")
else:
    print(f"❌ Model file NOT found at: {model_path}")
