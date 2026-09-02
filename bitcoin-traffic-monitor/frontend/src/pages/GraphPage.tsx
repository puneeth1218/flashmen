import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { GraphViewer } from '../components/GraphViewer';
import { fetchNetworkGraph, CytoscapeGraphResponse } from '../services/api';
import { GitFork, Filter } from 'lucide-react';

export const GraphPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const searchEntity = searchParams.get('search') || undefined;

  const [graphData, setGraphData] = useState<CytoscapeGraphResponse | null>(null);
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadGraph = async () => {
      setLoading(true);
      try {
        const data = await fetchNetworkGraph(searchEntity, depth);
        setGraphData(data);
      } catch (err) {
        console.error('Failed to load graph data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadGraph();
  }, [searchEntity, depth]);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <GitFork className="h-6 w-6 text-amber-500" />
            Interactive Topology Graph
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Visualizing P2P node connections and transaction peel-chain relationships.
            {searchEntity && (
              <span className="text-amber-400 font-mono ml-2">
                Focused on: {searchEntity}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-gray-800 p-2 rounded-lg border border-gray-700">
          <Filter className="h-4 w-4 text-gray-400" />
          <label className="text-xs text-gray-300">Traversal Depth:</label>
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="bg-gray-900 text-white text-xs border border-gray-700 rounded px-2 py-1 focus:outline-none"
          >
            <option value={1}>1 Hop</option>
            <option value={2}>2 Hops</option>
            <option value={3}>3 Hops</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-gray-400">
          Rendering network topology graph...
        </div>
      ) : (
        <GraphViewer graphData={graphData} />
      )}
    </div>
  );
};
