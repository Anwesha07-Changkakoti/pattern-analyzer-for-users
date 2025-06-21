import h337 from "heatmap.js";
import { useEffect, useRef } from "react";

export default function HeatmapViewer() {
  const containerRef = useRef(null);

  useEffect(() => {
    const fetchClicks = async () => {
      try {
        const res = await fetch("http://localhost:8000/heatmap/clicks");
        const data = await res.json();

        if (!containerRef.current) return;

        const heatmap = h337.create({
          container: containerRef.current,
          radius: 40,
        });

        heatmap.setData({
          max: 5,
          data: data.map((d) => ({
            x: d.x,
            y: d.y,
            value: 1,
          })),
        });
      } catch (err) {
        console.error("Failed to load heatmap data", err);
      }
    };

    fetchClicks();
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">Click Heatmap</h2>
      <div
        ref={containerRef}
        id="heatmapContainer"
        style={{
          width: "100%",
          height: "500px",
          position: "relative",
          border: "1px solid #444",
          borderRadius: "8px",
        }}
      />
    </div>
  );
}
