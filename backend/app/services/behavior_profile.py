from collections import Counter
from typing import List
import pandas as pd
import numpy as np
import datetime

def extract_behavior_features(logs_df: pd.DataFrame, user_id: str) -> dict:
    logs_df["login_hour"] = pd.to_datetime(logs_df["timestamp"]).dt.hour
    logs_df["weekday"] = pd.to_datetime(logs_df["timestamp"]).dt.dayofweek
    logs_df["file_type"] = logs_df["file_name"].str.extract(r"\.(\w+)$")[0].fillna("unknown")

    login_hour = logs_df["login_hour"].mean()
    files_per_day = logs_df.groupby(logs_df["timestamp"].str[:10]).size().mean()
    session_durations = logs_df.groupby("session_id")["duration"].sum()
    avg_duration = session_durations.mean() if not session_durations.empty else 0
    top_file_types = logs_df["file_type"].value_counts().head(3).index.tolist()
    top_regions = logs_df["ip_region"].value_counts().head(3).index.tolist()
    active_days = logs_df["weekday"].value_counts().head(3).index.tolist()

    return {
        "user_id": user_id,
        "avg_login_hour": login_hour,
        "avg_files_accessed": files_per_day,
        "avg_session_duration": avg_duration,
        "common_file_types": ",".join(top_file_types),
        "frequent_regions": ",".join(top_regions),
        "weekdays_active": ",".join(map(str, active_days))
    }
