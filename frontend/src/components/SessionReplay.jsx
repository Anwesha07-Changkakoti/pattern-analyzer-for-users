import { useEffect, useRef, useState } from "react";
import { Replayer } from "rrweb";
import "rrweb-player/dist/style.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function SessionReplay() {
  const containerRef = useRef(null);
  const [sessions, setSessions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch session list on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch(`${API_BASE}/session`);
        const data = await res.json();
        setSessions(data);
        if (data.length > 0) {
          setSelectedId(data[0].id); // auto-select latest
        }
      } catch (err) {
        setError("Failed to load session list.");
      }
    };
    fetchSessions();
  }, []);

  // When session ID changes, fetch and replay it
  useEffect(() => {
    if (!selectedId) return;
    const loadSession = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/session/${selectedId}?ts=${Date.now()}`);
        if (!res.ok) throw new Error("Session not found.");
        const data = await res.json();

        if (!data.events || data.events.length === 0) {
          setError("No session events found.");
          return;
        }

        const hasFullSnapshot = data.events.some((e) => e.type === 2);
        if (!hasFullSnapshot) {
          setError("Session has no full snapshot.");
          return;
        }

        const replayer = new Replayer(data.events, {
          root: containerRef.current,
          speed: 1,
          showDebug: false,
          UNSAFE_replayCanvas: true,
        });
        replayer.play();
      } catch (err) {
        console.error("❌ Error loading session:", err);
        setError("Error loading session playback.");
      } finally {
        setLoading(false);
      }
    };
    loadSession();
  }, [selectedId]);

  return (
    <div className="mt-8 text-white">
      <h2 className="text-xl font-semibold mb-4 text-lime-400">Session Playback</h2>

      <div className="mb-4">
        <label className="mr-2">Select session:</label>
        <select
          className="bg-black text-lime-400 border border-lime-500 px-2 py-1"
          onChange={(e) => setSelectedId(e.target.value)}
          value={selectedId || ""}
        >
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.created_at}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-yellow-400">Loading session...</p>}
      {error && <p className="text-red-500">{error}</p>}

      <div
        ref={containerRef}
        style={{
          border: "1px solid #444",
          borderRadius: "8px",
          background: "#fff",
          height: "500px",
          overflow: "hidden",
        }}
      />
    </div>
  );
}
