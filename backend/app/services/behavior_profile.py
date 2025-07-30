from collections import Counter, defaultdict
from datetime import datetime
import pytz
from typing import List
from app.models import ActivityLog, UserSession,UserBehaviorProfile
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def extract_behavior_features_from_activity(
    db: Session,
    logs: List[ActivityLog],
    sessions: List[UserSession],
    user_id: str
) -> dict:
    if not logs:
        raise ValueError("No activity logs provided")

    login_hours = []
    weekdays = []
    file_types = []
    regions = []
    file_access_by_day = defaultdict(int)

    ist = pytz.timezone("Asia/Kolkata")

    for log in logs:
        if log.timestamp:
        # Convert UTC timestamp to IST
           localized_time = log.timestamp.replace(tzinfo=pytz.utc).astimezone(ist)

           if log.action_type == "page_visit":
              login_hours.append(localized_time.hour)
              weekdays.append(localized_time.weekday())
           if log.action_type == "file_access":
               file_access_by_day[localized_time.date()] += 1

        if log.file_type:
           file_types.append(log.file_type)
        if log.region:
           regions.append(log.region)

    

    # --- Derived from sessions table ---
    session_durations = [s.duration for s in sessions if s.duration > 0]
    avg_session_duration = round(sum(session_durations) / len(session_durations), 2) if session_durations else 0.0
    total_time_spent = round(sum(session_durations), 2)

    # --- Files accessed per day ---
    avg_files_accessed = (
        round(sum(file_access_by_day.values()) / len(file_access_by_day), 2)
        if file_access_by_day else 0.0
    )

    # --- Top hours & days ---
    avg_login_hour = round(sum(login_hours) / len(login_hours), 2) if login_hours else 0.0
    weekday_counts = Counter(weekdays)
    top_weekdays = ",".join(str(day) for day, _ in weekday_counts.most_common(3))

    common_file_types = ",".join([ft for ft, _ in Counter(file_types).most_common(3)]) if file_types else ""
    frequent_regions = ",".join([r for r, _ in Counter(regions).most_common(3)]) if regions else ""

    return {
    "user_id": user_id,
    "avg_login_hour": avg_login_hour,
    "avg_session_duration": avg_session_duration,
    "total_time_spent": total_time_spent,
    "avg_files_accessed": avg_files_accessed,
    "common_file_types": common_file_types if common_file_types else "N/A",
    "frequent_regions": frequent_regions if frequent_regions else "N/A",
    "weekdays_active": top_weekdays if top_weekdays else "N/A"
}

from statistics import mean, stdev

def extract_behavior_profiles_for_all_users(
    db: Session,
    logs: List[ActivityLog],
    sessions: List[UserSession]
) -> List[dict]:
    profiles = []
    feature_vectors = []
    user_ids = []

    ist = pytz.timezone("Asia/Kolkata")
    logs_by_user = defaultdict(list)
    sessions_by_user = defaultdict(list)

    for log in logs:
        logs_by_user[log.user_id].append(log)
    for session in sessions:
        sessions_by_user[session.user_id].append(session)

    # Track global averages for tag computation
    all_upload_counts = []
    all_session_durations = []

    for user_id in logs_by_user:
        uploads = []
        for log in logs_by_user[user_id]:
            if log.action_type == "file_upload" or log.file_uploaded:
                uploads.append(log)
        all_upload_counts.append(len(uploads))

        durations = [s.duration for s in sessions_by_user[user_id] if s.duration]
        if durations:
            all_session_durations.append(mean(durations))

    global_upload_mean = mean(all_upload_counts) if all_upload_counts else 0
    global_upload_std = stdev(all_upload_counts) if len(all_upload_counts) > 1 else 0

    global_session_mean = mean(all_session_durations) if all_session_durations else 0
    global_session_std = stdev(all_session_durations) if len(all_session_durations) > 1 else 0

    for user_id, user_logs in logs_by_user.items():
        login_hours, weekdays, file_types, regions, ip_addresses = [], [], [], [], []
        file_access_by_day = defaultdict(int)
        uploads_by_day = defaultdict(int)
        time_spent_by_day = defaultdict(float)

        user_sessions = sessions_by_user.get(user_id, [])
        known_devices = set()
        known_ips = set()
        known_regions = set()

        for log in user_logs:
            if log.timestamp:
                localized = log.timestamp.replace(tzinfo=pytz.utc).astimezone(ist)
                if log.action_type == "page_visit":
                    login_hours.append(localized.hour)
                    weekdays.append(localized.weekday())
                if log.action_type == "file_access":
                    file_access_by_day[localized.date()] += 1
                if log.action_type == "file_upload" or log.file_uploaded:
                    uploads_by_day[localized.date()] += 1
                if log.ip_address:
                    ip_addresses.append(log.ip_address)
                    known_ips.add(log.ip_address)

            if log.file_type:
                file_types.append(log.file_type)
            if log.region:
                regions.append(log.region)
                known_regions.add(log.region)

        for session in user_sessions:
            if session.start_time:
                dt = session.start_time.replace(tzinfo=pytz.utc).astimezone(ist).date()
                time_spent_by_day[dt] += session.duration

        avg_session_duration = round(
            sum(s.duration for s in user_sessions if s.duration) / len(user_sessions), 2
        ) if user_sessions else 0.0

        total_time_spent = round(
            sum(s.duration for s in user_sessions), 2
        ) if user_sessions else 0.0

        avg_files_accessed = round(
            sum(file_access_by_day.values()) / len(file_access_by_day), 2
        ) if file_access_by_day else 0.0

        avg_login_hour = round(
            sum(login_hours) / len(login_hours), 2
        ) if login_hours else 0.0

        top_weekdays = ",".join(str(day) for day, _ in Counter(weekdays).most_common(3))
        common_file_types = ",".join(ft for ft, _ in Counter(file_types).most_common(3)) if file_types else ""
        frequent_regions = ",".join(r for r, _ in Counter(regions).most_common(3)) if regions else ""
        common_ips = ",".join(ip for ip, _ in Counter(ip_addresses).most_common(3)) if ip_addresses else ""
        total_uploads = sum(uploads_by_day.values())

        # 🔍 === TAGGING SECTION ===
        tags = []

        if avg_login_hour < 8 or avg_login_hour > 20:
            tags.append("Late Login")

        if global_upload_std > 0 and total_uploads > (global_upload_mean + global_upload_std):
            tags.append("Unusual Upload Volume")
        elif total_uploads > 10:
           tags.append("High Upload Activity")

        for ip in known_ips:
            if ip not in common_ips:
                tags.append("New IP Address")
                break

        for region in known_regions:
            if region not in frequent_regions:
                tags.append("New Region")
                break

        if global_session_std > 0 and avg_session_duration > (global_session_mean + 0.5 * global_session_std):
          tags.append("Extended Session")
        elif avg_session_duration > 1.0:
             tags.append("Long Sessions")

        # ===========

        user_ids.append(user_id)
        feature_vectors.append([
            avg_login_hour,
            avg_session_duration,
            avg_files_accessed,
            total_time_spent,
            total_uploads
        ])

        profiles.append({
            "user_id": user_id,
            "avg_login_hour": avg_login_hour,
            "avg_session_duration": avg_session_duration,
            "total_time_spent": total_time_spent,
            "avg_files_accessed": avg_files_accessed,
            "common_file_types": common_file_types if common_file_types else "N/A",
            "frequent_regions": frequent_regions if frequent_regions else "N/A",
            "weekdays_active": top_weekdays if top_weekdays else "N/A",
            "total_uploads": total_uploads,
            "file_uploads_by_day": dict(uploads_by_day),
            "time_spent_by_day": dict(time_spent_by_day),
            "ip_addresses": common_ips if common_ips else "N/A",
            "tags": tags,
            "anomaly_score": None  # Will be updated later
        })

    # ✅ Calculate anomaly scores
    if len(feature_vectors) >= 2:
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(feature_vectors)

        if len(feature_vectors) >= 5:
            model = IsolationForest(contamination=0.2, random_state=42)
            model.fit(X_scaled)
            raw_scores = model.decision_function(X_scaled)
            normalized_scores = [round(1 - score, 4) for score in raw_scores]
        else:
            # Fallback: distance from mean
            mean_vec = np.mean(X_scaled, axis=0)
            normalized_scores = [round(float(np.linalg.norm(vec - mean_vec)), 4) for vec in X_scaled]

        for i, score in enumerate(normalized_scores):
            profiles[i]["anomaly_score"] = score

    else:
        print("⚠️ Not enough users to compute anomaly scores (minimum 2 required).")

    return profiles
