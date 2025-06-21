import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function AnomalyBar({ summary }) {
  // Ensure summary is an object and has numeric values
  if (
    !summary ||
    typeof summary !== "object" ||
    isNaN(summary.anomalies) ||
    isNaN(summary.normal)
  )
    return null;

  const data = [
    { type: "Anomalies", count: Number(summary.anomalies) || 0 },
    { type: "Normal", count: Number(summary.normal) || 0 },
  ];

  return (
    <div className="h-64 bg-black border border-cybergreen p-4 rounded">
      <h3 className="text-green-400 text-lg font-bold mb-2">Anomaly Breakdown</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="type" stroke="#0f0" />
          <YAxis stroke="#0f0" />
          <Tooltip
            contentStyle={{ backgroundColor: "#111", borderColor: "#0f0", color: "#0f0" }}
            labelStyle={{ color: "#0f0" }}
          />
          <Bar dataKey="count" fill="#0f0" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
