import axios from "axios";
import { useEffect, useState } from "react";

export default function AllBehaviorProfiles() {
  const [profiles, setProfiles] = useState([]);

  useEffect(() => {
    axios
      .get(`${import.meta.env.VITE_API_BASE}/api/profile/all-profiles`)
      .then((res) => setProfiles(res.data))
      .catch(console.error);
  }, []);

  return (
    <div className="p-4 text-green-400 bg-black min-h-screen">
      <h2 className="text-3xl font-bold mb-6 border-b border-green-500 pb-2">
        All Users' Behavioral Profiles
      </h2>

      {profiles.map((profile) => (
        <div
          key={profile.user_id}
          className="border border-green-600 rounded-lg p-4 mb-6 shadow-lg"
        >
          <h3 className="text-xl font-bold text-green-300 mb-2">
            User: {profile.user_id}
          </h3>

          <p className="mb-1">
            <strong className="text-green-500">Active Weekdays:</strong>{" "}
            {profile.active_weekdays?.length > 0
              ? profile.active_weekdays.join(", ")
              : "N/A"}
          </p>

          <p className="mb-1">
            <strong className="text-green-500">IP Addresses:</strong>{" "}
            {profile.ip_addresses?.length > 0
              ? profile.ip_addresses.join(", ")
              : "N/A"}
          </p>

          <p className="mb-1">
            <strong className="text-green-500">Total Uploads:</strong>{" "}
            {profile.total_uploads ?? 0}
          </p>

          <p className="mb-3">
            <strong className="text-green-500">Total Time Spent:</strong>{" "}
            {profile.total_time_minutes?.toFixed(2) ?? 0} mins
          </p>
           <p className="mb-1">
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
               {profile.tags && profile.tags.length > 0 && (
                 <div className="mb-3 mt-2 flex flex-wrap gap-2">
                   {profile.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="bg-yellow-800 text-yellow-300 text-xs font-medium px-2 py-1 rounded-full"
                      >
                       {tag}
                     </span>
                   ))}
              </div>
            )}

          <div className="mb-2">
            <p className="font-semibold text-green-500">Uploads per Day:</p>
            <ul className="ml-4 list-disc">
              {Object.entries(profile.uploads_per_day || {}).map(
                ([day, count]) => (
                  <li key={day}>
                    {day}: {count} file{count !== 1 ? "s" : ""}
                  </li>
                )
              )}
            </ul>
          </div>

          <div>
            <p className="font-semibold text-green-500">Time Spent per Day:</p>
            <ul className="ml-4 list-disc">
              {Object.entries(profile.time_spent_per_day || {}).map(
                ([day, duration]) => (
                  <li key={day}>
                    {day}: {duration?.toFixed(2)} mins
                  </li>
                )
              )}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
}