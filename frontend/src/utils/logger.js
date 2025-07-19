import axios from "axios";
import deviceId from "./deviceId";

export function logActivity(action, extra = {}) {
  axios.post("http://localhost:8000/api/log", {
    deviceId,
    action,
    timestamp: new Date().toISOString(),
    ...extra
  }).catch(err => console.error("Log error:", err));
}
