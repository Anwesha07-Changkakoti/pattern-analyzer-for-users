import { useEffect, useRef, useState } from "react";
import simpleheat from "simpleheat";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function HeatmapViewer() {
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [allClicks, setAllClicks] = useState([]);
  const [showRaw, setShowRaw] = useState(true);
  const [timeRange, setTimeRange] = useState([0, 0]);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    loadHeatmap();
  }, []);

  const loadHeatmap = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    fetch(`${API_BASE}/heatmap/clicks`)
      .then((res) => res.json())
      .then((clicks) => {
        if (!Array.isArray(clicks)) return;

        const sorted = clicks
          .filter((d) => typeof d.x === "number" && typeof d.y === "number")
          .sort((a, b) => a.timestamp - b.timestamp);

        setAllClicks(sorted);

        const t0 = sorted[0]?.timestamp ?? 0;
        const t1 = sorted.at(-1)?.timestamp ?? 0;
        setTimeRange([t0, t1]);
        setCurrentTime(t1);

        drawHeatmap(sorted, t1);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Heatmap fetch error:", err);
        setLoading(false);
      });
  };

  const drawHeatmap = (clicks, time) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const visible = clicks.filter((d) => d.timestamp <= time);
    const heat = simpleheat(canvas);
    heat.data(visible.map((d) => [d.x, d.y, 1]));
    heat.max(5);
    heat.radius(40, 15);
    heat.draw();

    if (showRaw) {
      visible.forEach((d) => {
        ctx.fillStyle = "#00ff00";
        ctx.beginPath();
        ctx.arc(d.x, d.y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = await window?.user?.getIdToken?.();
      const res = await fetch(`${API_BASE}/upload-click-logs`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      const result = await res.json();
      alert(`Uploaded ${result.count} click records`);
      loadHeatmap();
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  return (
    <div className="p-6 text-white">
      <h2 className="text-xl font-bold text-cybergreen mb-4">📍 Click Heatmap Viewer</h2>

      <input type="file" onChange={handleUpload} className="mb-4 text-white" />

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
      {!loading && allClicks.length === 0 && (
        <p className="text-yellow-400 mt-4">No valid click data to render heatmap.</p>
      )}

      {allClicks.length > 0 && (
        <div className="mt-6 space-y-4">
          <label className="block text-cybergreen">
            ⏱️ Time Filter: {new Date(currentTime).toLocaleTimeString()}
          </label>
          <input
            type="range"
            min={timeRange[0]}
            max={timeRange[1]}
            value={currentTime}
            onChange={(e) => {
              const t = parseInt(e.target.value);
              setCurrentTime(t);
              drawHeatmap(allClicks, t);
            }}
            className="w-full"
          />

          <label className="flex items-center gap-2 text-white">
            <input
              type="checkbox"
              checked={showRaw}
              onChange={(e) => {
                setShowRaw(e.target.checked);
                drawHeatmap(allClicks, currentTime);
              }}
            />
            Show raw click points (green dots)
          </label>
        </div>
      )}
    </div>
  );
}
