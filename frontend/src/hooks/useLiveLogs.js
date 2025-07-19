// src/hooks/useLiveLogs.js
import { useEffect, useState } from "react";

export default function useLiveLogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stream"); // Use wss://your-vercel-url/ws/stream in production

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [data, ...prev.slice(0, 99)]);
      } catch (err) {
        console.error("WebSocket error:", err);
      }
    };

    return () => ws.close();
  }, []);

  return logs;
}
