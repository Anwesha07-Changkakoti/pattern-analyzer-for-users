import axios from "axios";
import { useEffect, useState } from "react";

const weekdayMap = {
  "0": "Sunday",
  "1": "Monday",
  "2": "Tuesday",
  "3": "Wednesday",
  "4": "Thursday",
  "5": "Friday",
  "6": "Saturday",
};

const tagColorMap = {
  "Extended Session": "bg-yellow-800 text-yellow-300",
  "Suspicious Uploads": "bg-red-800 text-red-300",
  "Unusual IP": "bg-purple-800 text-purple-300",
  "Night Activity": "bg-blue-800 text-blue-300",
};

export default function AllBehaviorProfiles() {
  const [profiles, setProfiles] = useState([]);
  const [expandedUsers, setExpandedUsers] = useState({});
  const [jointScores, setJointScores] = useState({}); // ✅ move here

  useEffect(() => {
    axios
      .get(`${import.meta.env.VITE_API_BASE}/api/profile/all-profiles`)
      .then((res) => setProfiles(res.data))
      .catch(console.error);
  }, []);

  const toggleExpand = async (userId) => {
    setExpandedUsers((prev) => ({
      ...prev,
      [userId]: !prev[userId],
    }));

    if (!jointScores[userId]) {
      try {
        const res = await axios.get(
          `${import.meta.env.VITE_API_BASE}/api/joint_score/${userId}`
        );
        setJointScores((prev) => ({
          ...prev,
          [userId]: res.data.joint_anomaly_score,
        }));
      } catch (err) {
        console.error("Error fetching joint score for", userId, err);
      }
    }
  };

  // ...rest of your component remains unchanged...


  const sortedProfiles = [...profiles].sort(
    (a, b) => b.anomaly_score - a.anomaly_score
  );

  return (
    <div className="p-4 text-green-400 bg-black min-h-screen">
      <h2 className="text-3xl font-bold mb-6 border-b border-green-500 pb-2">
        All Users' Behavioral Profiles
      </h2>

      {sortedProfiles.map((profile) => (
        <div
          key={profile.user_id}
          className="border border-green-600 rounded-lg p-4 mb-6 shadow-lg"
        >
          <h3 className="text-xl font-bold text-green-300 mb-2">
            User: {profile.user_id}
          </h3>

          <button
            className="text-green-400 underline text-sm mb-2"
            onClick={() => toggleExpand(profile.user_id)}
          >
            {expandedUsers[profile.user_id] ? "Collapse" : "Expand"}
          </button>

          {expandedUsers[profile.user_id] && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                <p>
                  <strong className="text-green-500">Avg Login Hour:</strong>{" "}
                  {profile.avg_login_hour ?? "N/A"}
                </p>

                <p>
                  <strong className="text-green-500">
                    Avg Session Duration:
                  </strong>{" "}
                  {(profile.avg_session_duration ?? 0).toFixed(2)} mins
                </p>

                <p>
                  <strong className="text-green-500">Total Time Spent:</strong>{" "}
                  {(profile.total_time_spent ?? 0).toFixed(2)} mins
                </p>

                <p>
                  <strong className="text-green-500">
                    Avg Files Accessed/Day:
                  </strong>{" "}
                  {profile.avg_files_accessed ?? "0"}
                </p>

                <p>
                  <strong className="text-green-500">File Types:</strong>{" "}
                  {profile.common_file_types ?? "N/A"}
                </p>

                <p>
                  <strong className="text-green-500">Regions:</strong>{" "}
                  {profile.frequent_regions ?? "N/A"}
                </p>

                <p>
                  <strong className="text-green-500">Active Weekdays:</strong>{" "}
                  {profile.weekdays_active
                    ? profile.weekdays_active
                        .split(",")
                        .map((d) => weekdayMap[d.trim()] ?? d)
                        .join(", ")
                    : "N/A"}
                </p>

                <p>
                  <strong className="text-green-500">IP Addresses:</strong>{" "}
                  {profile.ip_addresses ?? "N/A"}
                </p>

                <p>
                  <strong className="text-green-500">Total Uploads:</strong>{" "}
                  {profile.total_uploads ?? 0}
                </p>

                <p>
                  <strong className="text-green-500">Anomaly Score:</strong>{" "}
                  <span
                    className={
                      profile.anomaly_score > 0.6
                        ? "text-red-400 font-semibold"
                        : profile.anomaly_score > 0.3
                        ? "text-yellow-400 font-semibold"
                        : "text-green-400"
                    }
                  >
                    {profile.anomaly_score?.toFixed(4) ?? "N/A"}
                    {profile.anomaly_score > 0.6
                      ? " (High Risk ⚠️)"
                      : profile.anomaly_score > 0.3
                      ? " (Moderate)"
                      : " (Normal)"}
                  </span>
                </p>

                <p>
  <strong className="text-green-500">Joint Risk Score:</strong>{" "}
  {jointScores[profile.user_id] !== undefined ? (
    <span
      className={`${
        jointScores[profile.user_id] > 0.7
          ? "text-red-400 font-semibold"
          : jointScores[profile.user_id] > 0.4
          ? "text-yellow-400 font-semibold"
          : "text-green-400"
      }`}
    >
      {jointScores[profile.user_id].toFixed(4)}{" "}
      {jointScores[profile.user_id] > 0.7
        ? "(⚠ High Correlation)"
        : jointScores[profile.user_id] > 0.4
        ? "(Moderate)"
        : "(Normal)"}
    </span>
  ) : (
    <span className="text-gray-400">Loading...</span>
  )}
</p>

              </div>

              {profile.tags && profile.tags.length > 0 && (
                <div className="mb-3 mt-4 flex flex-wrap gap-2">
                  {profile.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className={`text-xs font-medium px-2 py-1 rounded-full ${
                        tagColorMap[tag] ??
                        "bg-yellow-800 text-yellow-300"
                      }`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="mt-4">
                <p className="font-semibold text-green-500 mb-1">
                  Uploads Per Day:
                </p>
                <ul className="ml-4 list-disc">
                  {Object.entries(profile.file_uploads_by_day || {}).map(
                    ([day, count]) => (
                      <li key={day}>
                        {day}: {count} file{count !== 1 ? "s" : ""}
                      </li>
                    )
                  )}
                </ul>
              </div>

              <div className="mt-4">
                <p className="font-semibold text-green-500 mb-1">
                  Time Spent Per Day:
                </p>
                <ul className="ml-4 list-disc">
                  {Object.entries(profile.time_spent_by_day || {}).map(
                    ([day, duration]) => (
                      <li key={day}>
                        {day}: {(duration ?? 0).toFixed(2)} mins
                      </li>
                    )
                  )}
                </ul>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
