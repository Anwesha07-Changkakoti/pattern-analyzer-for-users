from collections import Counter
from typing import List
import pandas as pd
import numpy as np
import datetime

def extract_behavior_features(logs_df: pd.DataFrame, user_id: str) -> dict:
    print("==== Behavior Extraction Debug ====")
    print("Columns:", logs_df.columns.tolist())
    print(logs_df[["timestamp", "file_name", "session_id", "duration", "ip_region"]].head())
    logs_df["timestamp"] = pd.to_datetime(logs_df["timestamp"], errors="coerce")
    logs_df = logs_df.dropna(subset=["timestamp"])

    logs_df["login_hour"] = logs_df["timestamp"].dt.hour
    logs_df["weekday"] = logs_df["timestamp"].dt.dayofweek

    if "file_name" not in logs_df.columns:
        logs_df["file_name"] = "unknown.csv"

    logs_df["file_type"] = logs_df["file_name"].astype(str).str.extract(r"\.(\w+)$")[0].fillna("unknown")

    login_hour = logs_df["login_hour"].mean() if not logs_df["login_hour"].empty else 0

    files_per_day = (
        logs_df.groupby(logs_df["timestamp"].dt.date).size().mean()
        if not logs_df.empty else 0
    )

    session_durations = logs_df.groupby("session_id")["duration"].sum()
    avg_duration = session_durations.mean() if not session_durations.empty else 0

    top_file_types = logs_df["file_type"].value_counts().head(3).index.tolist()
    top_regions = logs_df["ip_region"].value_counts().head(3).index.tolist()
    active_days = logs_df["weekday"].value_counts().head(3).index.tolist()
    session_trend = (
        logs_df.groupby(logs_df["timestamp"].dt.strftime("%Y-%m-%d"))["duration"]
        .mean()
        .reset_index()
        .rename(columns={"duration": "avg_duration", "timestamp": "date"})
    )

    print("Session Trend Preview:")
    print(session_trend.head())

    return {
        "user_id": user_id,
        "avg_login_hour": login_hour,
        "avg_files_accessed": files_per_day,
        "avg_session_duration": avg_duration,
        "common_file_types": ",".join(top_file_types),
        "frequent_regions": ",".join(top_regions),
        "weekdays_active": ",".join(map(str, active_days))
    }
