let socket;

export function getSocket() {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    socket = new WebSocket(import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/stream");
  }
  return socket;
}
