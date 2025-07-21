import axios from "axios";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { useEffect, useState } from "react";
import { useAuthState } from "react-firebase-hooks/auth";
import { Bar, BarChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { auth } from "../firebase";

const BehaviorProfile = () => {
  const [user] = useAuthState(auth);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = await user.getIdToken();

        // ✅ Fixed: Use the correct working endpoint
        const res = await axios.get(
          `${import.meta.env.VITE_API_BASE}/api/profile/stats`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setProfile(res.data);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch profile.");
      }
    };

    if (user) {
      fetchProfile();
    }
  }, [user]);

  const exportToPDF = () => {
    const input = document.getElementById("profile-content");
    html2canvas(input).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF();
      const imgWidth = 190;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 10, 10, imgWidth, imgHeight);
      pdf.save("behavior-profile.pdf");
    });
  };

  if (error) {
    return <div className="text-red-500 text-center mt-10">{error}</div>;
  }

  if (!profile) {
    return <div className="text-white text-center mt-10">Loading profile...</div>;
  }

  // Recharts expects data as array of objects
  const barData = [
    {
      name: "Login Hour",
      value: profile.avg_login_hour,
    },
    {
      name: "Files Accessed",
      value: profile.avg_files_accessed,
    },
    {
      name: "Session Duration",
      value: profile.avg_session_duration,
    },
  ];

  return (
    <div className="text-white p-8">
      <h2 className="text-2xl font-bold mb-6 text-center text-green-400">User Behavior Profile</h2>

      <div id="profile-content" className="bg-gray-900 rounded-lg p-6 shadow-md">
        <p><strong>Average Login Hour:</strong> {profile.avg_login_hour}</p>
        <p><strong>Average Files Accessed Per Day:</strong> {profile.avg_files_accessed}</p>
        <p><strong>Average Session Duration (mins):</strong> {profile.avg_session_duration}</p>
        <p><strong>Most Active Day:</strong> {profile.most_active_day}</p>
        <p><strong>Most Active Region:</strong> {profile.most_active_region}</p>

        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2 text-green-300">Behavior Chart</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <XAxis dataKey="name" stroke="#ccc" />
              <YAxis stroke="#ccc" />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="text-center mt-6">
        <button
          onClick={exportToPDF}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded"
        >
          Export as PDF
        </button>
      </div>
    </div>
  );
};

export default BehaviorProfile;
