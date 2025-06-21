export default function DataTable({ rows, title, height = 300 }) {
  if (!Array.isArray(rows) || rows.length === 0) return null;

  const firstRow = rows[0];
  if (!firstRow || typeof firstRow !== "object") return null;

  const columns = Object.keys(firstRow);

  return (
    <div className="mb-4">
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <div
        className="overflow-y-auto border border-cybergreen rounded"
        style={{ maxHeight: height }}
      >
        <table className="min-w-full text-sm table-fixed">
          <thead className="sticky top-0 bg-black z-10">
            <tr>
              <th className="px-2 py-1 border-b border-cybergreen text-left">#</th>
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
            {rows.map((row, i) => (
              <tr
                key={i}
                className={
                  row.anomaly === 1
                    ? "bg-red-800 text-white"
                    : i % 2 === 0
                    ? "bg-black"
                    : "bg-gray-900"
                }
              >
                <td className="px-2 py-1 border-b border-cybergreen">{i + 1}</td>
                {columns.map((col) => {
                  const val = row[col];

                  // Safely render value
                  const safeValue =
                    val === null || val === undefined
                      ? ""
                      : typeof val === "object"
                      ? JSON.stringify(val)
                      : String(val);

                  return (
                    <td
                      key={col}
                      className={`px-2 py-1 border-b border-cybergreen ${
                        col === "anomaly_reason" ? "italic text-green-400" : ""
                      }`}
                      title={col === "anomaly_reason" ? safeValue : undefined}
                    >
                      {safeValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
