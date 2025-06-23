import axios from "axios";
import { getAuth } from "firebase/auth";
import html2pdf from "html2pdf.js";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis, YAxis
} from "recharts";

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

  const chartData = [
    { name: "Login Hour", value: profile.avg_login_hour },
    { name: "Files/Day", value: profile.avg_files_accessed },
    { name: "Session Duration (s)", value: profile.avg_session_duration },
  ];

  const exportPDF = () => {
    const element = document.getElementById("profile-section");
    html2pdf().from(element).save("behavior-profile.pdf");
  };

  return (
    <div className="p-6 max-w-xl mx-auto mt-10">
      <div id="profile-section" className="bg-white rounded-2xl shadow-lg p-6">
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

        {/* Chart */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Behavior Overview</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Export Button */}
      <div className="text-center mt-4">
        <button
          onClick={exportPDF}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
        >
          Export as PDF
        </button>
      </div>
    </div>
  );
}
