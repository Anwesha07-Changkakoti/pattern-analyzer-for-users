import h337 from "heatmap.js";
import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function HeatmapViewer() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const container = document.getElementById("heatmapContainer");
    if (!container) return;

    fetch(`${API_BASE}/heatmap/clicks`)
      .then((res) => res.json())
      .then((clicks) => {
        const points = clicks.map((d) => ({
          x: d.x,
          y: d.y,
          value: 1,
        }));

        const heatmapInstance = h337.create({
          container,
          radius: 40,
          maxOpacity: 0.6,
          minOpacity: 0,
          blur: 0.85,
          useCanvasExt: true, // ✅ Important: Use safer canvas rendering
        });

        heatmapInstance.setData({
          max: 5,
          data: points,
        });

        setLoading(false);
      })
      .catch((err) => {
        console.error("Heatmap fetch error:", err);
      });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-cybergreen mb-4">Click Heatmap</h2>
      <div
        id="heatmapContainer"
        style={{
          width: "100%",
          height: "600px",
          position: "relative",
          backgroundColor: "#111",
        }}
      />
      {loading && <p className="text-cybergreen mt-4">Loading heatmap…</p>}
    </div>
  );
}
