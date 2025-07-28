import pandas as pd
import numpy as np
import hashlib
import logging
import os
import gc
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from typing import List, Tuple, Union
from functools import lru_cache

from app.database import SessionLocal
from app.models import AnalysisResult
from app.services.behavior_profile import extract_behavior_features_from_activity
from app.services.profile_updater import upsert_behavior_profile

# --- Logging Setup ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/anomaly_detection.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

MODEL_VERSION = "LightIF_v1.0"
MAX_RECORDS = 1000  # Render-safe limit

@lru_cache(maxsize=25)
def hash_dataframe(df: pd.DataFrame) -> str:
    df.columns = df.columns.map(str)
    df.index = df.index.map(str)
    df = df.sort_index(axis=1)
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()

# --- Feature Preparation ---
def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    df = df.select_dtypes(include="number").fillna(0)
    if df.empty:
        raise ValueError("No numeric columns after filtering.")
    scaler = StandardScaler()
    return pd.DataFrame(scaler.fit_transform(df), columns=df.columns, index=df.index)

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = validate_schema(df)
    return numeric_df

def fallback_anomaly_detection(df: pd.DataFrame, z_threshold: float = 3.0) -> List[int]:
    try:
        mean = df.mean()
        std = df.std(ddof=0) + 1e-9
        z_scores = ((df - mean).abs() / std).max(axis=1)
        return [1 if z > z_threshold else 0 for z in z_scores]
    except Exception as e:
        logging.error(f"Fallback detection failed: {e}")
        return [0] * len(df)

def _compute_reasons(df: pd.DataFrame, preds: List[int], top_n: int = 3) -> List[str]:
    try:
        med = df.median()
        mad = (df - med).abs().median() + 1e-9
        reasons = []
        for idx, (i, row) in enumerate(df.iterrows()):
            if preds[idx] == 0:
                reasons.append("")
                continue
            z_scores = ((row - med).abs() / mad)
            z_scores_sorted = z_scores.sort_values(ascending=False)
            top_features = [f"{str(f)} (z={z_scores[f]:.2f})" for f in z_scores_sorted.head(top_n).index]
            reasons.append(f"Deviation: {', '.join(top_features)}")
        return reasons
    except Exception as e:
        logging.error(f"Failed to compute reasons: {e}")
        return ["Reason computation error"] * len(preds)

def _log_anomalies(df: pd.DataFrame, preds: List[int], reasons: List[str]) -> None:
    try:
        for idx, (row, pred, why) in enumerate(zip(df.iterrows(), preds, reasons)):
            if pred == 1 and idx < 10:
                logging.info(
                    f"[{MODEL_VERSION}] Anomaly at index {idx} | Reason: {why} | Row: {row[1].to_dict()}"
                )
    except Exception as e:
        logging.error(f"Anomaly logging failed: {e}")

def _store_summary(user_uid: str, file_name: str, total_records: int, anomaly_count: int, df_with_preds: pd.DataFrame) -> None:
    db = SessionLocal()
    try:
        db.add(AnalysisResult(
            user_id=user_uid,
            file_name=file_name,
            total_records=total_records,
            anomaly_count=anomaly_count,
            timestamp=datetime.utcnow(),
        ))
        try:
            behavior_features = extract_behavior_features_from_activity(df_with_preds, user_uid)
            upsert_behavior_profile(db, behavior_features)
        except Exception as e:
            logging.error(f"[{MODEL_VERSION}] Behavior profile update failed: {e}")
        db.commit()
    finally:
        db.close()

# --- Main Detection Function ---
def detect_anomalies(
    df_raw: pd.DataFrame,
    *,
    user_uid: str,
    file_name: str,
    contamination: float = 0.1,
    return_reasons: bool = False,
    return_df: bool = False,
) -> Union[List[int], Tuple[List[int], List[str]], pd.DataFrame]:

    if len(df_raw) > MAX_RECORDS:
        raise ValueError(f"Too many records: {len(df_raw)} (limit: {MAX_RECORDS})")

    df_raw.columns = [
        f"col_{i}" if not col or str(col).startswith("Unnamed") else str(col)
        for i, col in enumerate(df_raw.columns)
    ]

    try:
        df_proc = prepare_features(df_raw)
    except Exception as e:
        logging.error(f"[{MODEL_VERSION}] Feature preparation failed: {e}")
        raise

    if len(df_proc) < 10:
        logging.warning(f"[{MODEL_VERSION}] Too few records; using fallback logic.")
        preds = fallback_anomaly_detection(df_proc)
        reasons = ["Fallback logic due to few records"] * len(preds)
    else:
        try:
            df_hash = hash_dataframe(df_proc)
        except Exception:
            df_hash = None

        adaptive_contamination = max(0.01, min(contamination, 1.0 / len(df_proc)))
        model = IsolationForest(contamination=adaptive_contamination, random_state=42)
        model.fit(df_proc)
        pred_raw = model.predict(df_proc)
        preds = [1 if p == -1 else 0 for p in pred_raw]
        reasons = _compute_reasons(df_proc, preds)

    _store_summary(
        user_uid=user_uid,
        file_name=file_name,
        total_records=len(preds),
        anomaly_count=sum(preds),
        df_with_preds=df_raw.assign(anomaly=preds)
    )

    _log_anomalies(df_proc, preds, reasons)

    del df_proc
    gc.collect()

    if return_df:
        return df_raw.assign(anomaly=preds)
    return (preds, reasons) if return_reasons else preds