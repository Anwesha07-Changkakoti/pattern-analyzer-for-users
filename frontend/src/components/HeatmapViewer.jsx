import h337 from "heatmap.js";
import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function HeatmapViewer() {
  const heatmapRef = useRef(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const container = heatmapRef.current;
    if (!container) return;

    const heatmapInstance = h337.create({
      container,
      radius: 40,
      maxOpacity: 0.6,
      minOpacity: 0,
      blur: 0.9,
      gradient: {
        0.2: "#00ff00",
        0.5: "#ffff00",
        0.9: "#ff0000",
      },
    });

    fetch(`${API_BASE}/heatmap/clicks`)
      .then((res) => res.json())
      .then((clicks) => {
        if (!Array.isArray(clicks)) return;

        const points = clicks.map((d) => ({
          x: d.x,
          y: d.y,
          value: 1,
        }));

        heatmapInstance.setData({
          max: 5,
          data: points,
        });

        setLoading(false);
      })
      .catch((err) => {
        console.error("Heatmap fetch error:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-cybergreen mb-4">Click Heatmap</h2>
      <div
        ref={heatmapRef}
        style={{
          width: "100%",
          height: "600px",
          position: "relative",
          background: "#111",
          overflow: "hidden",
        }}
      />
      {loading && <p className="text-cybergreen mt-4">Loading heatmap…</p>}
    </div>
  );
}
