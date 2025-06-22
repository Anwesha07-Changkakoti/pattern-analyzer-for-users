import { useEffect, useRef, useState } from "react";
import { Replayer } from "rrweb";
import "rrweb-player/dist/style.css"; // Optional: include rrweb default styles

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function SessionReplay() {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const res = await fetch(`${API_BASE}/session/latest`);
        if (!res.ok) throw new Error("Failed to fetch session data");

        const data = await res.json();
        console.log("🔍 Loaded session data:", data); // Debug log

        if (!data?.events || data.events.length === 0) {
          setError("No session data found.");
          return;
        }

        // Check if at least one full snapshot exists (type: 2)
        const hasFullSnapshot = data.events.some((e) => e.type === 2);
        if (!hasFullSnapshot) {
          setError("Session does not contain a full snapshot.");
          return;
        }

        const replayer = new Replayer(data.events, {
          root: containerRef.current,
          showDebug: false, // change to true if debugging
          speed: 1,
          UNSAFE_replayCanvas: true,
        });

        replayer.play();
      } catch (err) {
        console.error("❌ Session playback error:", err);
        setError("Error loading session playback.");
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, []);

  return (
    <div className="mt-8">
      <h2 className="text-xl font-semibold mb-4">Session Playback</h2>
      {loading && <p>Loading session...</p>}
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
