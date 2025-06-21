import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

import AdminDashboard from "../pages/AdminDashboard";
import AnomalyBar from "./AnomalyBar";
import AnomalyLineChart from "./AnomalyLineChart";
import AnomalyPie from "./AnomalyPie";
import DataTable from "./DataTable";
import HeatmapChart from "./HeatmapChart";
import Home from "./Home";
import LiveBarChart from "./LiveBarChart";
import Login from "./Login";
import Navbar from "./Navbar";
import ProtectedRoute from "./ProtectedRoute";
import ResultsHistory from "./ResultsHistory";
import StatsCard from "./StatsCard";
import Unauthorized from "./Unauthorized";
import Upload from "./Upload";

/* ───────────────────────────────────────── env config ── */
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const WS_BASE  = import.meta.env.VITE_WS_BASE  ?? "ws://localhost:8000/ws/stream";

export default function App() {
  const { user, role, loading: authLoading, login } = useAuth();

  const [summary,   setSummary]   = useState(null);
  const [fullBatch, setFullBatch] = useState([]);
  const [batchRows, setBatchRows] = useState([]);
  const [liveRows,  setLiveRows]  = useState([]);
  const [busy,      setBusy]      = useState(false);
  const [fileId,    setFileId]    = useState(null);

  /* ─────────────────────────────── helpers ── */
  const authHeader = async () =>
    user ? { Authorization: `Bearer ${await user.getIdToken()}` } : {};

  /* ───────────────────────────── file upload ── */
  const onUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const { data } = await axios.post(`${API_BASE}/analyze`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          ...(await authHeader()),
        },
        maxBodyLength: Infinity,
      });

      setSummary(data.summary);
      setFullBatch(data.rows);
      setFileId(data.file_id);
      setBatchRows([]);
    } catch (err) {
      console.error(err);
      alert("Upload failed — check backend, CORS, or auth.");
    } finally {
      setBusy(false);
    }
  };

  /* ─────────────────────────── download CSV ── */
  const handleDownload = async () => {
    try {
      const token = await user.getIdToken();
      const res   = await fetch(`${API_BASE}/download/${fileId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Download failed");

      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = Object.assign(document.createElement("a"), {
        href: url,
        download: "anomalies.csv",
      });
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Download failed. Check auth or backend.");
    }
  };

  /* ───────── stream batch rows gradually to UI ── */
  useEffect(() => {
    if (!fullBatch.length) return;
    let idx = 0;
    const CHUNK = 50;
    const id = setInterval(() => {
      setBatchRows((prev) => [...prev, ...fullBatch.slice(idx, idx + CHUNK)]);
      idx += CHUNK;
      if (idx >= fullBatch.length) clearInterval(id);
    }, 100);
    return () => clearInterval(id);
  }, [fullBatch]);

  /* ─────────────────────────── WebSocket live feed ── */
  const wsRef = useRef(null);
  useEffect(() => {
    if (authLoading || !user) return;

    let retryTimer;

    const connect = async () => {
      const token = await user.getIdToken();
      if (!token) {
        retryTimer = setTimeout(connect, 5000);
        return;
      }

      const ws = new WebSocket(`${WS_BASE}?token=${token}`);
      wsRef.current = ws;

      ws.onopen    = () => console.log("✅ WebSocket connected");
      ws.onmessage = (evt) =>
        setLiveRows((prev) => [JSON.parse(evt.data), ...prev].slice(0, 100));
      ws.onerror   = (e) => console.error("WebSocket error", e);
      ws.onclose   = () => {
        console.warn("🔌 WebSocket closed, retrying in 5 s");
        retryTimer = setTimeout(connect, 5000);
      };
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [authLoading, user]);

  if (authLoading) return <p className="p-6 text-cybergreen">Loading authentication…</p>;

  /* ─────────────────────────── render ── */
  return (
    <div className="min-h-screen bg-black text-cybergreen">
      <Navbar />

      {!user ? (
        <GuestView onLogin={login} />
      ) : (
        <Dashboard
          role={role}
          busy={busy}
          onUpload={onUpload}
          summary={summary}
          batchRows={batchRows}
          liveRows={liveRows}
          lineChartData={batchRows.map((r, i) => ({
            index: i,
            anomaly: Number(r.Anomaly ?? r.anomaly ?? 0),
          }))}
          fileId={fileId}
          onDownload={handleDownload}
        />
      )}

      {/* routes */}
      <Routes>
        <Route path="/"          element={<Home />} />
        <Route path="/login"     element={<Login />} />
        <Route path="/upload"    element={<ProtectedRoute><Upload /></ProtectedRoute>} />
        <Route path="/history"   element={<ResultsHistory />} />
        <Route path="/admin"     element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
        <Route path="/unauthorized" element={<Unauthorized />} />
      </Routes>
    </div>
  );
}

/* ───────── sub‑components for clarity ───────── */

function GuestView({ onLogin }) {
  return (
    <div className="p-6 text-center">
      <h1 className="text-3xl font-bold mb-4">User Pattern Analyzer</h1>
      <p className="mb-4">Please log in to view the dashboard.</p>
      <button
        onClick={onLogin}
        className="px-4 py-2 bg-cybergreen text-black rounded hover:bg-green-700"
      >
        Login
      </button>
    </div>
  );
}

function Dashboard({
  role,
  busy,
  onUpload,
  summary,
  batchRows,
  liveRows,
  lineChartData,
  fileId,
  onDownload,
}) {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">User Pattern Analyzer</h1>

      {role !== "viewer" && (
        <>
          <label className="inline-block px-4 py-2 bg-cybergreen text-black rounded cursor-pointer">
            Upload Log
            <input type="file" onChange={onUpload} className="hidden" />
          </label>
          {busy && <p>Uploading…</p>}
        </>
      )}

      {summary && (
        <>
          {/* stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatsCard title="Total"     value={summary.total}     />
            <StatsCard title="Anomalies" value={summary.anomalies} />
            <StatsCard title="Normal"    value={summary.normal}    />
          </div>

          {/* pie & bar */}
          <div className="grid grid-cols-2 gap-4">
            <AnomalyPie summary={summary} />
            <AnomalyBar summary={summary} />
          </div>

          {/* line + table */}
          {Array.isArray(batchRows) && batchRows.length > 0 && (
            <>
              <AnomalyLineChart data={lineChartData} />
              <DataTable rows={batchRows} title="Batch Results (streamed)" height={400} />
            </>
          )}

          {/* heatmap */}
          {fileId && <HeatmapChart fileId={fileId} />}

          {/* download */}
          {fileId && (
            <button onClick={onDownload} className="underline text-cybergreen">
              Download Anomalies CSV
            </button>
          )}
        </>
      )}

      {/* live stream */}
      <h2 className="text-2xl font-bold">Real‑Time Stream</h2>
      {Array.isArray(liveRows) && liveRows.length > 0 && (
        <>
          <DataTable rows={liveRows} title="Live Logs (last 100)" height={300} />
          <LiveBarChart dataStream={liveRows} />
        </>
      )}
    </div>
  );
}
