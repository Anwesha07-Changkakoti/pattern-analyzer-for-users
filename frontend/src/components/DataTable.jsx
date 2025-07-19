export default function DataTable({ rows, title, height = 300 }) {
  if (!rows || !rows.length) return null;

  const baseColumns = Object.keys(rows[0]);
  const hasAnomaly = baseColumns.includes("anomaly") || baseColumns.includes("Anomaly");
  const columns = hasAnomaly ? [...baseColumns, "status"] : baseColumns;

  return (
    <div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <div
        className="overflow-y-auto border border-cybergreen"
        style={{ maxHeight: height }}
      >
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-black">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-2 py-1 border-b border-cybergreen text-left capitalize"
                >
                  {col.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const isAnomaly =
                row.anomaly === 1 ||
                row.anomaly === true ||
                row.Anomaly === 1;

              return (
                <tr
                  key={i}
                  className={isAnomaly ? "bg-red-900 text-white" : ""}
                >
                  {columns.map((col) => {
                    if (col === "status" && hasAnomaly) {
                      return (
                        <td key={col} className="px-2 py-1 border-b border-cybergreen">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              isAnomaly
                                ? "bg-red-600 text-white"
                                : "bg-green-700 text-white"
                            }`}
                          >
                            {isAnomaly ? "Anomaly" : "Normal"}
                          </span>
                        </td>
                      );
                    }

                    return (
                      <td
                        key={col}
                        className={`px-2 py-1 border-b border-cybergreen ${
                          col === "anomaly_reason" ? "italic text-green-400" : ""
                        }`}
                        title={col === "anomaly_reason" ? row[col] : undefined}
                      >
                        {String(row[col] ?? "")}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
