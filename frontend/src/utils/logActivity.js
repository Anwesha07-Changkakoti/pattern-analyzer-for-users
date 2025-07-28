import axios from "axios";
import { getAuth, onAuthStateChanged } from "firebase/auth";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function logActivity(deviceId, actionType, pathname, details = null) {
  const auth = getAuth();

  return new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        console.warn("⚠️ No Firebase user signed in — cannot log activity.");
        unsubscribe();
        return resolve(); // no error, just skip
      }

      try {
        const token = await user.getIdToken(true);

        const payload = {
          deviceId,
          action_type: actionType,
          pathname,
          timestamp: new Date().toISOString(),
          details,
        };

        await axios.post(`${API_BASE}/api/log`, payload, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        console.log("✅ Activity logged:", payload);
        resolve();
      } catch (error) {
        console.error("❌ Activity logging failed:", error?.response?.data || error.message);
        reject(error);
      } finally {
        unsubscribe();
      }
    });
  });
}