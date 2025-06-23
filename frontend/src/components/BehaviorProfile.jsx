import axios from "axios";
import { getAuth } from "firebase/auth";
import { useEffect, useState } from "react";

export default function BehaviorProfile() {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const auth = getAuth();
        const user = auth.currentUser;

        if (!user) {
          setError("User not logged in");
          return;
        }

        const token = await user.getIdToken();

        const res = await axios.get(`${import.meta.env.VITE_API_BASE}/profile/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        console.log("Profile data received:", res.data);
        setProfile(res.data);
      } catch (err) {
        setError("Failed to fetch behavior profile");
        console.error(err);
      }
    };

    fetchProfile();
  }, []);

  if (error) return <div className="text-center text-red-500 mt-8">{error}</div>;
  if (!profile) return <div className="text-center text-gray-500 mt-8">Loading profile...</div>;

  const safe = (val, decimals = 2) =>
    typeof val === "number" ? val.toFixed(decimals) : "N/A";

  const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const formattedWeekdays = (profile.weekdays_active || "")
    .split(",")
    .map(w => weekdays[parseInt(w)])
    .filter(Boolean)
    .join(", ");

  return (
    <div className="p-6 bg-white rounded-2xl shadow-lg max-w-xl mx-auto mt-10">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">User Behavior Profile</h2>
      <ul className="space-y-2 text-gray-700 text-base">
        <li><strong>Avg. Login Hour:</strong> {safe(profile.avg_login_hour)}</li>
        <li><strong>Files Accessed/Day:</strong> {safe(profile.avg_files_accessed)}</li>
        <li className={profile.avg_session_duration > 600 ? "text-red-600 font-semibold" : ""}>
          <strong>Avg. Session Duration:</strong> {safe(profile.avg_session_duration)}s
        </li>
        <li><strong>Common File Types:</strong> {profile.common_file_types || "N/A"}</li>
        <li><strong>Frequent Regions:</strong> {profile.frequent_regions || "N/A"}</li>
        <li><strong>Active Weekdays:</strong> {formattedWeekdays || "N/A"}</li>
      </ul>
    </div>
  );
}
