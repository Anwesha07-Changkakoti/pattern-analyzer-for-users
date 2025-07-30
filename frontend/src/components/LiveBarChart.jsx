import html2canvas from "html2canvas";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function LiveBarChart({ dataStream }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();

      // Filter logs from the last 10 seconds
      const recentLogs = dataStream.filter((log) => {
        const ts = new Date(log.timestamp);
        return now - ts < 10000;
      });

      // Group by second
      const grouped = {};
      recentLogs.forEach((log) => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        grouped[time] = (grouped[time] || 0) + 1;
      });

      const updated = Object.entries(grouped).map(([time, count]) => ({
        time,
        count,
      }));

      // Ensure chart always has 10 seconds of data
      const timeNow = new Date();
      const filled = [];
      for (let i = 9; i >= 0; i--) {
        const t = new Date(timeNow.getTime() - i * 1000).toLocaleTimeString();
        const existing = updated.find((u) => u.time === t);
        filled.push({ time: t, count: existing ? existing.count : 0 });
      }

      setChartData(filled);
    }, 1000);

    return () => clearInterval(interval);
  }, [dataStream]);

  const handleDownload = () => {
    const chart = document.getElementById("live-chart");
    html2canvas(chart).then((canvas) => {
      const link = document.createElement("a");
      link.download = "live_bar_chart.png";
      link.href = canvas.toDataURL();
      link.click();
    });
  };

  // ✅ Normalize anomaly field handling
  const anomalyCount = dataStream
    .slice(-10)
    .filter((log) => Number(log.anomaly ?? log.Anomaly ?? 0) === 1).length;

  // Optional debug:
  // console.log("Live chart data:", chartData);

  return (
    <div className="border border-cybergreen rounded p-4 mt-8" id="live-chart">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl font-bold text-cybergreen">Live Bar Chart</h2>
        <button
          onClick={handleDownload}
          className="bg-cybergreen text-black px-3 py-1 rounded"
        >
          Download PNG
        </button>
      </div>
      <p className="text-cybergreen font-mono text-sm mb-1">
        Anomalies (last 10): {anomalyCount}
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <XAxis dataKey="time" tick={{ fill: "#00FF00" }} />
          <YAxis tick={{ fill: "#00FF00" }} />
          <Tooltip contentStyle={{ backgroundColor: "#222", color: "#00FF00" }} />
          <Legend />
          <Bar dataKey="count" fill="#32CD32" name="Live Packet Count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

