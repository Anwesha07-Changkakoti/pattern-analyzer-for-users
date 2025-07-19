// src/contexts/WebSocketContext.jsx
import { createContext, useContext, useEffect, useRef, useState } from "react";

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [latestLog, setLatestLog] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stream");
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        setLatestLog(log);
      } catch (e) {
        console.error("Invalid WebSocket message", e);
      }
    };

    ws.onclose = () => {
      console.warn("WebSocket closed. Reconnecting in 3s...");
      setTimeout(() => window.location.reload(), 3000);
    };

    ws.onerror = (e) => {
      console.error("WebSocket error:", e);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ latestLog }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
