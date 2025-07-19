import axios from "axios";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import html2pdf from "html2pdf.js";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import usePageLogger from "../hooks/usePageLogger";

export default function BehaviorProfile() {
  usePageLogger();
  const [profile, setProfile] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [extraStats, setExtraStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const auth = getAuth();
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        console.warn("User not logged in");
        setError("User not logged in");
        return;
      }

      try {
        const token = await user.getIdToken(true);

        // Update profile from activity
        await axios.post(
          `${import.meta.env.VITE_API_BASE}/api/profile/update-from-activity`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );

        // Fetch behavior profile
        const profileRes = await axios.get(
          `${import.meta.env.VITE_API_BASE}/api/profile`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setProfile(profileRes.data);

        // Fetch session trend
        const trendRes = await axios.get(
          `${import.meta.env.VITE_API_BASE}/api/profile/session-trend`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setTrendData(trendRes.data);

        // Fetch extended stats
        const statsRes = await axios.get(
          `${import.meta.env.VITE_API_BASE}/api/profile/stats`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        setExtraStats({
          ip_address: statsRes.data.ip_addresses?.[0] || "N/A",
          total_sessions: statsRes.data.session_count,
          uploads_today: statsRes.data.upload_count_today,
          total_time: statsRes.data.total_duration_minutes,
          anomaly: statsRes.data.anomalies?.length > 0,
          anomalyList: statsRes.data.anomalies || [],
        });
      } catch (err) {
        console.error("Token or request error:", err);
        setError("Failed to fetch profile.");
      }
    });

    return () => unsubscribe();
  }, []);

  const exportPDF = () => {
    const element = document.getElementById("profile-section");
    html2pdf().from(element).save("behavior-profile.pdf");
  };

  const safe = (val, decimals = 2) =>
    typeof val === "number" ? val.toFixed(decimals) : "N/A";

  if (error)
    return <div className="text-center text-red-500 mt-8">{error}</div>;

  if (!profile)
    return (
      <div className="text-center text-gray-500 mt-8">Loading profile...</div>
    );

  const weekdays = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];
  const formattedWeekdays = (profile.weekdays_active || "")
    .split(",")
    .map((w) => weekdays[parseInt(w)])
    .filter(Boolean)
    .join(", ");

  const chartData = [
    { name: "Login Hour", value: profile.avg_login_hour },
    { name: "Files/Day", value: profile.avg_files_accessed },
    { name: "Session Duration (s)", value: profile.avg_session_duration },
  ];

  return (
    <div className="p-6 max-w-xl mx-auto mt-10">
      <div
        id="profile-section"
        className={`rounded-2xl shadow-lg p-6 ${
          extraStats?.anomaly
            ? "bg-red-50 border-red-500 border-2"
            : "bg-white"
        }`}
      >
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          User Behavior Profile
        </h2>
        <ul className="space-y-2 text-gray-700 text-base">
          <li>
            <strong>Avg. Login Hour:</strong>{" "}
            {safe(profile.avg_login_hour)}
          </li>
          <li>
            <strong>Files Accessed/Day:</strong>{" "}
            {safe(profile.avg_files_accessed)}
          </li>
          <li
            className={
              profile.avg_session_duration > 600
                ? "text-red-600 font-semibold"
                : ""
            }
          >
            <strong>Avg. Session Duration:</strong>{" "}
            {safe(profile.avg_session_duration)}s
          </li>
          <li>
            <strong>Common File Types:</strong>{" "}
            {profile.common_file_types || "N/A"}
          </li>
          <li>
            <strong>Frequent Regions:</strong>{" "}
            {profile.frequent_regions || "N/A"}
          </li>
          <li>
            <strong>Active Weekdays:</strong>{" "}
            {formattedWeekdays || "N/A"}
          </li>

          {extraStats && (
            <>
              <li>
                <strong>IP Address:</strong>{" "}
                {extraStats.ip_address || "N/A"}
              </li>
              <li>
                <strong>Total Sessions:</strong>{" "}
                {extraStats.total_sessions ?? "0"}
              </li>
              <li>
                <strong>Uploads Today:</strong>{" "}
                {extraStats.uploads_today ?? 0}
              </li>
              <li>
                <strong>Total Time Spent:</strong>{" "}
                {safe(extraStats.total_time)} minutes
              </li>
              {extraStats.anomaly && (
                <li>
                  <strong className="text-red-600">Anomalies Detected:</strong>
                  <ul className="list-disc list-inside text-red-500 ml-2 mt-1">
                    {extraStats.anomalyList.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </li>
              )}
            </>
          )}
        </ul>

        {/* Bar Chart */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Behavior Overview
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Line Chart */}
        {Array.isArray(trendData) && trendData.length > 0 && (
          <div className="mt-10">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Weekly Session Duration
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={trendData}
                margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="duration"
                  stroke="#10b981"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
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
