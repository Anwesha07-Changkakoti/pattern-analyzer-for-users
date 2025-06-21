import axios from "axios";
import { useEffect, useState } from "react";
import HeatMap from "react-heatmap-grid";

/**
 * Props:
 *   fileId – the file_id returned by /analyze
 */
export default function HeatmapChart({ fileId }) {
  const [xLabels] = useState([...Array(24).keys()]); // 0‑23
  const [yLabels, setYLabels] = useState([]);
  const [dataMatrix, setDataMatrix] = useState([]);

  useEffect(() => {
    if (!fileId) return; // wait until we have an analysis result

    axios
      .get(
        `https://user-pattern-analyzer.onrender.com/analytics/heatmap/${fileId}`
      )
      .then((res) => {
        setYLabels(Object.keys(res.data.data));   // Monday‑Sunday
        setDataMatrix(Object.values(res.data.data));
      })
      .catch((err) => console.error("Heatmap fetch error", err));
  }, [fileId]);

  if (!fileId) return null;

  return (
    <div className="p-4 border border-green-500 rounded-xl m-4 bg-black">
      <h2 className="text-green-400 text-xl mb-2">
        Time‑Based Anomaly Heatmap
      </h2>
      <HeatMap
        xLabels={xLabels}
        yLabels={yLabels}
        data={dataMatrix}
        squares
        cellStyle={(_, value) => ({
          background: `rgba(255,0,0,${Math.min(value / 10, 1)})`,
          color: "white",
          fontSize: "12px",
        })}
        cellRender={(value) => (value ? value : "")}
      />
    </div>
  );
}
