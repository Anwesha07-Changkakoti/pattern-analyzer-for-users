import axios from "axios";
import { useEffect, useRef, useState } from "react";
import LiveBarChart from "../components/LiveBarChart";
import { getSocket } from "../utils/socket";

export default function AdminDashboard() {
  const [deviceIds, setDeviceIds] = useState([]);
  const [anomalies, setAnomalies] = useState({});
  const [logs, setLogs] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [deviceFilter, setDeviceFilter] = useState("");
  const [pathFilter, setPathFilter] = useState("");
  const containerRef = useRef(null);

  const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

  useEffect(() => {
    axios.get(`${API_BASE}/api/devices`)
      .then(res => setDeviceIds(res.data.devices))
      .catch(err => console.error("Error fetching devices:", err));
  }, []);

  useEffect(() => {
    deviceIds.forEach(id => {
      axios.get(`${API_BASE}/api/check/${id}`)
        .then(res => {
          setAnomalies(prev => ({
            ...prev,
            [id]: res.data
          }));
        })
        .catch(err => console.error(`Error checking anomaly for ${id}:`, err));
    });
  }, [deviceIds]);

  useEffect(() => {
    const socket = getSocket();
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        setLogs(prev => {
          const isDuplicate = prev.some(log =>
            (log.id && data.id && log.id === data.id) ||
            (
              log.timestamp === data.timestamp &&
              log.device_id === data.device_id &&
              log.pathname === data.pathname
            )
          );

          if (isDuplicate) return prev;

          return [data, ...prev].slice(0, 100);
        });
      } catch (err) {
        console.error("WebSocket parse error:", err);
      }
    };

    return () => {
      socket.onmessage = null;
    };
  }, []);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter(log =>
    (!deviceFilter || log.device_id.includes(deviceFilter)) &&
    (!pathFilter || log.pathname.includes(pathFilter))
  );

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-cybergreen mb-4">Admin Dashboard</h2>
      <p className="mb-6">List of all devices using the app and their anomaly status.</p>

      {/* ✅ Anomaly Status Table */}
      {deviceIds.length === 0 ? (
        <p>No device logs found.</p>
      ) : (
        <table className="w-full table-auto border-collapse border border-gray-700 mb-10">
          <thead>
            <tr className="bg-gray-800 text-cybergreen">
              <th className="border border-gray-700 px-4 py-2">Device ID</th>
              <th className="border border-gray-700 px-4 py-2">Status</th>
              <th className="border border-gray-700 px-4 py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {deviceIds.map(id => (
              <tr key={id} className="text-white">
                <td className="border border-gray-700 px-4 py-2">{id}</td>
                <td className="border border-gray-700 px-4 py-2">
                  {anomalies[id]?.anomalous ? "⚠️ Anomalous" : "✅ Normal"}
                </td>
                <td className="border border-gray-700 px-4 py-2">
                  {anomalies[id]?.reason || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ✅ Real-Time Logs */}
      <h3 className="text-xl font-bold text-cybergreen mt-8 mb-2">Real-Time Stream</h3>

      <div className="flex gap-4 mb-3">
        <input
          placeholder="Filter by Device ID"
          className="bg-black border border-cybergreen text-cybergreen px-2 py-1"
          onChange={(e) => setDeviceFilter(e.target.value)}
        />
        <input
          placeholder="Filter by Pathname"
          className="bg-black border border-cybergreen text-cybergreen px-2 py-1"
          onChange={(e) => setPathFilter(e.target.value)}
        />
        <button
          onClick={() => setAutoScroll(!autoScroll)}
          className="bg-cybergreen text-black px-4 py-2 rounded"
        >
          {autoScroll ? "Pause Auto-Scroll" : "Resume Auto-Scroll"}
        </button>
      </div>

      <div
        ref={containerRef}
        className="max-h-96 overflow-y-auto bg-black border border-cybergreen p-4"
      >
        <table className="w-full text-sm text-white">
          <thead>
            <tr className="text-cybergreen border-b border-cybergreen">
              <th className="text-left py-1">Time</th>
              <th className="text-left py-1">Device</th>
              <th className="text-left py-1">Action</th>
              <th className="text-left py-1">Path</th>
              <th className="text-left py-1">Details</th>
              <th className="text-left py-1">IP</th>
              <th className="text-left py-1">Anomaly</th> {/* ✅ NEW COLUMN */}
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map((log, i) => (
              <tr
                key={i}
                className={`border-b border-gray-700 ${log.anomaly === 1 ? "bg-red-800 text-white" : ""}`}
              >
                <td>{new Date(log.timestamp).toLocaleTimeString()}</td>
                <td>{log.device_id}</td>
                <td>{log.action_type}</td>
                <td>{log.pathname}</td>
                <td>{log.details ?? ""}</td>
                <td>{log.ip_address ?? "—"}</td>
                <td>{log.anomaly === 1 ? "⚠️ Anomalous" : "✅ Normal"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ✅ Live Chart */}
      <div className="mt-6">
        <LiveBarChart dataStream={logs} />
      </div>
    </div>
  );
}
