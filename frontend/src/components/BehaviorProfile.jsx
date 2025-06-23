import axios from "axios";
import { useEffect, useState } from "react";

export default function BehaviorProfile() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
  axios.get(`${import.meta.env.VITE_API_BASE}/api/profile/`)
    .then(res => {
      console.log("Profile data received:", res.data);  // ✅ ADD THIS
      setProfile(res.data);
    })
    .catch(err => console.error("Failed to fetch behavior profile", err));
}, []);


  if (!profile) return <div>Loading profile...</div>;

  const safe = (val, decimals = 2) =>
    typeof val === "number" ? val.toFixed(decimals) : "N/A";

  return (
    <div className="p-4 bg-white rounded shadow max-w-xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">User Behavior Profile</h2>
      <ul className="space-y-2">
        <li><strong>Avg. Login Hour:</strong> {safe(profile.avg_login_hour)}</li>
        <li><strong>Files Accessed/Day:</strong> {safe(profile.avg_files_accessed)}</li>
        <li><strong>Avg. Session Duration:</strong> {safe(profile.avg_session_duration)}s</li>
        <li><strong>Common File Types:</strong> {profile.common_file_types || "N/A"}</li>
        <li><strong>Frequent Regions:</strong> {profile.frequent_regions || "N/A"}</li>
        <li><strong>Active Weekdays:</strong> {profile.weekdays_active || "N/A"}</li>
      </ul>
    </div>
  );
}
