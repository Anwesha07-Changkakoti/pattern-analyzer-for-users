import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COLORS = ["#39FF14", "#FF0000"];

export default function AnomalyPie({ summary }) {
  // Validate input
  const isValid =
    summary &&
    typeof summary.normal === "number" &&
    typeof summary.anomalies === "number" &&
    (summary.normal + summary.anomalies) > 0;

  if (!isValid) {
    return (
      <div className="text-red-500 border border-red-700 p-2 rounded bg-black">
        Pie chart cannot render due to invalid or missing summary data.
      </div>
    );
  }

  const data = [
    { name: "Normal", value: summary.normal },
    { name: "Anomalies", value: summary.anomalies },
  ];

  const total = summary.normal + summary.anomalies;

  const renderLabel = ({ name, value }) => {
    const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
    return `${name}: ${percent}%`;
  };

  return (
    <div className="h-64">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={80}
            dataKey="value"
            label={renderLabel}
            isAnimationActive={false}
          >
            {data.map((entry, idx) => (
              <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${value} logs`} />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
