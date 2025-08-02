from app.database import SessionLocal
from app.models import ActivityLog, UserSession
from app.services.behavior_profile import extract_behavior_profiles_for_all_users
from app.services.behavior_profile import save_profiles_to_db  # import function from step 1

def run():
    db = SessionLocal()
    logs = db.query(ActivityLog).all()
    sessions = db.query(UserSession).all()

    profiles = extract_behavior_profiles_for_all_users(db, logs, sessions)
    save_profiles_to_db(db, profiles)

    print(f"✅ {len(profiles)} behavior profiles saved to DB")
    db.close()

if __name__ == "__main__":
    run()
