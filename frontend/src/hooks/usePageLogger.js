import axios from "axios";
import { getAuth } from "firebase/auth";
import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function usePageLogger() {
  const location = useLocation();

  useEffect(() => {
  let deviceId = localStorage.getItem("deviceId");
  if (!deviceId) {
    deviceId = uuidv4();
    localStorage.setItem("deviceId", deviceId);
  }

  const lastLoggedPath = sessionStorage.getItem("lastLoggedPath");
  const lastLoggedTime = sessionStorage.getItem("lastLoggedTime");
  const now = Date.now();

  if (
    lastLoggedPath === location.pathname &&
    lastLoggedTime &&
    now - parseInt(lastLoggedTime, 10) < 5000
  ) {
    console.log("🛑 Skipping duplicate log for", location.pathname);
    return;
  }

  const auth = getAuth();
  const user = auth.currentUser;

  if (!user) {
    console.warn("⚠️ User not signed in; skipping log.");
    return;
  }

  user.getIdToken()
    .then((token) => {
      const log = {
        deviceId,
        action_type: "page_visit",
        timestamp: new Date().toISOString(),
        pathname: location.pathname,
        details: "Visited via logger hook",
      };

      return axios.post(`${API_BASE}/api/log`, log, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    })
    .then(() => {
      sessionStorage.setItem("lastLoggedPath", location.pathname);
      sessionStorage.setItem("lastLoggedTime", now.toString());
      console.log("✅ Page visit logged:", location.pathname);
    })
    .catch((err) => {
      console.error("❌ Error logging page visit:", err.response?.data || err.message);
    });

}, [location.pathname]);

}
