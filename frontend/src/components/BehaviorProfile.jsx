import axios from "axios";
import { useEffect, useState } from "react";

export default function BehaviorProfile() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    axios.get("/api/profile")  // <-- you'll create this endpoint next
      .then(res => setProfile(res.data))
      .catch(err => console.error("Failed to fetch behavior profile", err));
  }, []);

  if (!profile) return <div>Loading profile...</div>;

  return (
    <div className="p-4 bg-white rounded shadow max-w-xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">User Behavior Profile</h2>
      <ul className="space-y-2">
        <li><strong>Avg. Login Hour:</strong> {profile.avg_login_hour.toFixed(2)}</li>
        <li><strong>Files Accessed/Day:</strong> {profile.avg_files_accessed.toFixed(2)}</li>
        <li><strong>Avg. Session Duration:</strong> {profile.avg_session_duration.toFixed(2)}s</li>
        <li><strong>Common File Types:</strong> {profile.common_file_types}</li>
        <li><strong>Frequent Regions:</strong> {profile.frequent_regions}</li>
        <li><strong>Active Weekdays:</strong> {profile.weekdays_active}</li>
      </ul>
    </div>
  );
}
