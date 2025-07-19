import axios from "axios";
import { useEffect, useState } from "react";

export default function AllBehaviorProfiles() {
  const [profiles, setProfiles] = useState([]);

  useEffect(() => {
    axios.get(`${import.meta.env.VITE_API_BASE}/api/profile/all-profiles`)
      .then((res) => setProfiles(res.data))
      .catch(console.error);
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">All Users' Behavioral Profiles</h2>
      {profiles.map(profile => (
        <div key={profile.user_id} className="border rounded-xl p-4 shadow mb-6">
          <h3 className="text-lg font-semibold">User: {profile.user_id}</h3>
          <p><strong>Active Weekdays:</strong> {profile.active_weekdays.join(", ")}</p>
          <p><strong>IP Addresses:</strong> {profile.ip_addresses.join(", ")}</p>
          <p><strong>Uploads per Day:</strong></p>
          <ul className="ml-4">
            {Object.entries(profile.uploads_per_day).map(([day, count]) => (
              <li key={day}>{day}: {count} files</li>
            ))}
          </ul>
          <p><strong>Time Spent per Day:</strong></p>
          <ul className="ml-4">
            {Object.entries(profile.time_spent_per_day).map(([day, duration]) => (
              <li key={day}>{day}: {duration.toFixed(2)} mins</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
