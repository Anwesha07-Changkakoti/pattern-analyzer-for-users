// App.jsx 
import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { record } from "rrweb";
import { useAuth } from "../contexts/AuthContext";
import useLiveLogs from "../hooks/useLiveLogs";
import usePageLogger from "../hooks/usePageLogger";
import AdminDashboard from "../pages/AdminDashboard";
import "../utils/deviceId";
import AllBehaviorProfiles from "./AllBehaviorProfiles";
import BehaviorProfile from "./BehaviorProfile";
import HeatmapViewer from "./HeatmapViewer";
import Home from "./Home";
import Login from "./Login";
import Navbar from "./Navbar";
import PathFlowChart from "./PathFlowChart";
import ProtectedRoute from "./ProtectedRoute";
import ResultsHistory from "./ResultsHistory";
import SessionReplay from "./SessionReplay";
import Unauthorized from "./Unauthorized";
import Upload from "./Upload";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function App() {
  const liveLogs = useLiveLogs();
  usePageLogger();
  const { user, loading: authLoading, login } = useAuth();
  const location = useLocation();
  const deviceId = localStorage.getItem("deviceId") ?? "anonymous_device";

  // 👆 Track page clicks
  useEffect(() => {
    const allowedPaths = ["/", "/heatmap", "/history"];
    if (!allowedPaths.includes(location.pathname) || !user) return;

    const handleClick = (e) => {
      fetch(`${API_BASE}/clicks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          x: e.clientX,
          y: e.clientY,
          pathname: location.pathname,
          timestamp: Date.now(),
        }),
      });
    };

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [location.pathname, user]);

  // 👆 Track session events
  useEffect(() => {
    const events = [];
    const stop = record({ emit: (event) => events.push(event), recordCanvas: true });
    if (typeof record.takeFullSnapshot === "function") record.takeFullSnapshot();

    const flush = () => {
      if (events.length === 0 || !events.some((e) => e.type === 2)) return;
      navigator.sendBeacon(
        `${API_BASE}/session`,
        new Blob([JSON.stringify({ events })], { type: "application/json" })
      );
      events.length = 0;
    };

    const timer = setInterval(flush, 10000);
    window.addEventListener("beforeunload", flush);
    return () => {
      stop();
      flush();
      clearInterval(timer);
      window.removeEventListener("beforeunload", flush);
    };
  }, []);

  // 👆 Track navigation paths
  useEffect(() => {
     if (!user) return;
    //logActivity(deviceId, "page_visit", location.pathname);
    fetch(`${API_BASE}/path`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pathname: location.pathname, timestamp: Date.now() }),
    });
  }, [location]);

  if (authLoading) {
    return <p className="p-6 text-cybergreen">Loading authentication…</p>;
  }

  return (
    <div className="min-h-screen bg-black text-cybergreen">
      <Navbar />

      {!user ? (
        <div className="p-6 text-center">
          <h1 className="text-3xl font-bold mb-4">User Pattern Analyzer</h1>
          <p className="mb-4">Please log in to view the dashboard.</p>
          <button
            onClick={login}
            className="px-4 py-2 bg-cybergreen text-black rounded hover:bg-green-700"
          >
            Login
          </button>
        </div>
      ) : (
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/history" element={<ResultsHistory />} />
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="/heatmap" element={<ProtectedRoute role="admin"><HeatmapViewer /></ProtectedRoute>} />
          <Route path="/replay" element={<ProtectedRoute role="admin"><SessionReplay /></ProtectedRoute>} />
          <Route path="/session" element={<ProtectedRoute role="admin"><SessionReplay /></ProtectedRoute>} />
          <Route path="/flow" element={<ProtectedRoute role="admin"><PathFlowChart /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute role="admin"><BehaviorProfile /></ProtectedRoute>} />
          <Route path="/all-behaviors" element={<AllBehaviorProfiles />} />
        </Routes>
      )}
    </div>
  );
}
