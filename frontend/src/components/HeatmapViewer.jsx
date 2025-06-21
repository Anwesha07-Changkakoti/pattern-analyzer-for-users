// src/components/HeatmapViewer.jsx

import { useEffect, useRef, useState } from "react";
import simpleheat from "simpleheat";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function HeatmapViewer() {
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    fetch(`${API_BASE}/heatmap/clicks`)
      .then((res) => res.json())
      .then((clicks) => {
        if (!Array.isArray(clicks)) return;

        const points = clicks
          .filter((d) => typeof d.x === "number" && typeof d.y === "number")
          .map((d) => [d.x, d.y, 1]); // simpleheat expects [x, y, value]

        if (points.length > 0) {
          const heat = simpleheat(canvas);
          heat.data(points);
          heat.max(5);
          heat.radius(40, 15); // (radius, blur)
          heat.draw();
          setHasData(true);
        }

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
      <canvas
        ref={canvasRef}
        width={window.innerWidth - 100}
        height={600}
        style={{
          display: "block",
          background: "#111",
          border: "1px solid #444",
        }}
      />
      {loading && <p className="text-cybergreen mt-4">Loading heatmap…</p>}
      {!loading && !hasData && (
        <p className="text-yellow-400 mt-4">No valid click data to render heatmap.</p>
      )}
    </div>
  );
}
