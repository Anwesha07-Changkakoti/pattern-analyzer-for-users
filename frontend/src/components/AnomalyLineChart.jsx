import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function AnomalyLineChart({ data }) {
  if (
    !Array.isArray(data) ||
    data.length === 0 ||
    typeof data[0] !== "object"
  )
    return null;

  // Ensure anomaly field is numeric and present
  const filteredData = data.filter(
    (item) => typeof item.anomaly === "number"
  );
  if (filteredData.length === 0) return null;

  const hasTimestamp = "timestamp" in filteredData[0];

  return (
    <div className="bg-black border border-cybergreen rounded p-4">
      <h2 className="text-xl font-bold text-cybergreen mb-4">
        Anomaly Timeline
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={filteredData}>
          <CartesianGrid stroke="#444" strokeDasharray="3 3" />
          <XAxis
            dataKey={hasTimestamp ? "timestamp" : "index"}
            stroke="#00FF00"
            tick={{ fill: "#00FF00", fontSize: 12 }}
            minTickGap={20}
          />
          <YAxis
            stroke="#00FF00"
            tick={{ fill: "#00FF00", fontSize: 12 }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#111", borderColor: "#0f0" }}
            labelStyle={{ color: "#0f0" }}
            formatter={(value, name) => [
              value,
              name === "anomaly" ? "Anomaly Score" : name,
            ]}
          />
          <Legend verticalAlign="top" height={36} />
          <Line
            type="monotone"
            dataKey="anomaly"
            stroke="#FF4C4C"
            strokeWidth={2}
            dot={false}
            name="Anomalies"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
