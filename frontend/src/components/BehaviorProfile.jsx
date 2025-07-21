import { onAuthStateChanged } from "firebase/auth";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { auth } from "../firebase";

const COLORS = ["#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#0088FE"];

export default function BehaviorProfile() {
  const [profile, setProfile] = useState(null);
  const [user, setUser] = useState(null);

  // Listen to auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
    });
    return () => unsubscribe();
  }, []);

  // Fetch behavior profile once user is available
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = await user.getIdToken();

        // Step 1: POST to update behavior profile from activity
        await fetch("http://localhost:8000/api/profile/update-from-activity", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        // Step 2: GET the profile data
        const res = await fetch("http://localhost:8000/api/profile", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();
        setProfile(data);
      } catch (error) {
        console.error("Error loading behavior profile:", error);
      }
    };

    if (user) {
      fetchProfile();
    }
  }, [user]);

  const exportAsPDF = () => {
    const input = document.getElementById("profile-chart");
    html2canvas(input).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF();
      pdf.addImage(imgData, "PNG", 10, 10, 190, 0);
      pdf.save("behavior-profile.pdf");
    });
  };

  if (!profile) return <div className="text-white p-4">Loading behavior profile...</div>;

  return (
    <div className="p-4 text-white">
      <h2 className="text-2xl font-bold mb-4">Behavior Profile</h2>
      <button
        onClick={exportAsPDF}
        className="mb-4 px-4 py-2 bg-green-600 hover:bg-green-700 rounded"
      >
        Export as PDF
      </button>

      <div id="profile-chart" className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bar Chart for Login Hours */}
        <div className="bg-gray-900 p-4 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-2">Login Hour Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={profile.login_hour_distribution}>
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#00C49F" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart for File Types */}
        <div className="bg-gray-900 p-4 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-2">File Types Accessed</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={profile.file_types_accessed}
                dataKey="count"
                nameKey="type"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {profile.file_types_accessed.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart for Session Duration */}
        <div className="bg-gray-900 p-4 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-2">Average Session Duration</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={profile.session_duration}>
              <XAxis dataKey="user" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avg_duration" fill="#FFBB28" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart for Day-of-Week Activity */}
        <div className="bg-gray-900 p-4 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-2">Day of Week Activity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={profile.day_of_week_activity}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
