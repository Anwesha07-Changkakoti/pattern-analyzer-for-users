import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import usePageLogger from "../hooks/usePageLogger"; // ✅ Properly imported
import { logActivity } from "../utils/logActivity";
import AnomalyBar from "./AnomalyBar";
import AnomalyLineChart from "./AnomalyLineChart";
import AnomalyPie from "./AnomalyPie";
import DataTable from "./DataTable";
import LiveBarChart from "./LiveBarChart";
import StatsCard from "./StatsCard";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_BASE ?? "ws://localhost:8000";
const WS_PATH = "/ws/stream";

export default function Home() {
  usePageLogger(); // ✅ Will log page visit
  const { user } = useAuth();
  const deviceId = localStorage.getItem("deviceId") ?? "anonymous_device";

  const [summary, setSummary] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [fullBatch, setFullBatch] = useState([]);
  const [batchRows, setBatchRows] = useState([]);
  const [liveRows, setLiveRows] = useState([]);
  const [busy, setBusy] = useState(false);

  const [deviceFilter, setDeviceFilter] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef(null);

  const authHeader = async () => {
    if (!user) return {};
    const token = await user.getIdToken();
    return { Authorization: `Bearer ${token}` };
  };

  const onUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    logActivity(deviceId, "file_upload_start", file.name);
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

      logActivity(deviceId, "file_upload_success", file.name);
      setSummary(data.summary);
      setFullBatch(data.rows);
      setFileId(data.file_id);
      setBatchRows([]);
    } catch (err) {
      logActivity(deviceId, "file_upload_fail", file.name);
      console.error(err);
      alert("Upload failed — check backend, CORS, or auth.");
    } finally {
      setBusy(false);
    }
  };

  const handleDownload = async () => {
    try {
      const token = await user.getIdToken();
      const response = await fetch(`${API_BASE}/download/${fileId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "anomalies.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Download failed. Check auth or backend.");
    }
  };

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

  const wsRef = useRef(null);
  useEffect(() => {
    const connect = async () => {
      const token = user ? await user.getIdToken() : "";
      const ws = new WebSocket(`${WS_BASE}${WS_PATH}?token=${token}`);
      wsRef.current = ws;

      ws.onmessage = (evt) => {
        const row = JSON.parse(evt.data);

        setLiveRows((prev) => {
          const isDuplicate = prev.some((existing) =>
            (existing.id && row.id && existing.id === row.id) ||
            (
              existing.timestamp === row.timestamp &&
              existing.device_id === row.device_id &&
              existing.pathname === row.pathname
            )
          );
          if (isDuplicate) return prev;
          return [row, ...prev].slice(0, 100);
        });
      };

      ws.onclose = () => setTimeout(connect, 5000);
    };

    connect();
    return () => wsRef.current?.close();
  }, [user]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [liveRows, autoScroll]);

  const lineChartData = batchRows.map((row, idx) => ({
    index: idx,
    anomaly: Number(row.Anomaly ?? row.anomaly ?? 0),
  }));

  const filteredLiveRows = liveRows.filter(
    (row) =>
      row.device_id?.toLowerCase().includes(deviceFilter.toLowerCase()) &&
      row.pathname?.toLowerCase().includes(pathFilter.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Welcome to the User Pattern Analyzer</h1>

      <label className="inline-block px-4 py-2 bg-cybergreen text-black rounded cursor-pointer">
        Upload Log
        <input type="file" onChange={onUpload} className="hidden" />
      </label>
      {busy && <p>Uploading…</p>}

      {summary && (
        <>
          <div className="grid grid-cols-3 gap-4 mt-4">
            <StatsCard title="Total" value={summary.total} />
            <StatsCard title="Anomalies" value={summary.anomalies} />
            <StatsCard title="Normal" value={summary.normal} />
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <AnomalyPie summary={summary} />
            <AnomalyBar summary={summary} />
          </div>
          <AnomalyLineChart data={lineChartData} />
          <DataTable rows={batchRows} title="Batch Results (streamed)" height={400} />
          {fileId && (
            <button onClick={handleDownload} className="underline text-cybergreen">
              Download Anomalies CSV
            </button>
          )}
        </>
      )}

      <h2 className="text-2xl font-bold mt-8">Real‑Time Stream</h2>

      <div className="flex items-center gap-4 mb-2">
        <input
          type="text"
          placeholder="Filter by Device ID"
          className="bg-black border border-green-500 text-green-300 px-2 py-1 rounded"
          value={deviceFilter}
          onChange={(e) => setDeviceFilter(e.target.value)}
        />
        <input
          type="text"
          placeholder="Filter by Pathname"
          className="bg-black border border-green-500 text-green-300 px-2 py-1 rounded"
          value={pathFilter}
          onChange={(e) => setPathFilter(e.target.value)}
        />
        <button
          onClick={() => setAutoScroll((prev) => !prev)}
          className="bg-cybergreen text-black px-4 py-1 rounded"
        >
          {autoScroll ? "Pause Auto-Scroll" : "Resume Auto-Scroll"}
        </button>
      </div>

      <DataTable rows={filteredLiveRows} title="Live Logs (last 100)" height={300} />
      <div ref={logsEndRef} />

      <AnomalyLineChart
        data={liveRows.map((row, idx) => ({
          index: idx,
          anomaly: Number(row.anomaly ?? 0),
        }))}
      />

      <LiveBarChart dataStream={liveRows} />
    </div>
  );
}
