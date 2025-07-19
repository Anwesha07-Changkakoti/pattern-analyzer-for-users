import { useEffect, useState } from "react";
import { ResponsiveContainer, Sankey, Tooltip } from "recharts";

export default function PathFlowChart() {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPathFlow = async () => {
      try {
        const res = await fetch("http://localhost:8000/paths/flow");
        if (!res.ok) throw new Error("Failed to fetch path flow");

        const data = await res.json();
        setNodes(data.nodes);
        setLinks(data.links);
      } catch (err) {
        console.error(err);
        setError("Error loading navigation flow.");
      } finally {
        setLoading(false);
      }
    };

    fetchPathFlow();
  }, []);

  return (
    <div className="mt-8">
      <h2 className="text-xl font-semibold mb-4">Page Navigation Flow</h2>
      {loading && <p>Loading flow...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && (
        <ResponsiveContainer width="100%" height={400}>
          <Sankey
            data={{ nodes, links }}
            node={{ padding: 20, width: 15 }}
            link={{ stroke: "#77c", strokeOpacity: 0.4 }}
          >
            <Tooltip />
          </Sankey>
        </ResponsiveContainer>
      )}
    </div>
  );
}
