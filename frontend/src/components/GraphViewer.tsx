import React from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { CytoscapeGraphResponse } from '../services/api';

interface GraphViewerProps {
  graphData: CytoscapeGraphResponse | null;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({ graphData }) => {
  if (!graphData) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-900 rounded-xl border border-gray-800 text-gray-500">
        Loading Cytoscape network graph...
      </div>
    );
  }

  // Transform graphData nodes & edges to Cytoscape element format
  const elements = [
    ...graphData.nodes.map((node) => ({
      data: {
        id: node.data.id,
        label: node.data.label,
        type: node.data.type,
        risk: node.data.risk_score || 0,
      },
    })),
    ...graphData.edges.map((edge) => ({
      data: {
        id: edge.data.id,
        source: edge.data.source,
        target: edge.data.target,
        label: edge.data.label || '',
      },
    })),
  ];

  const stylesheet: cytoscape.Stylesheet[] = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'background-color': '#3b82f6',
        color: '#ffffff',
        'font-size': '10px',
        'text-valign': 'bottom',
        'text-margin-y': 4,
      },
    },
    {
      selector: 'node[type = "ip"]',
      style: {
        'background-color': '#10b981',
        shape: 'ellipse',
      },
    },
    {
      selector: 'node[type = "wallet"]',
      style: {
        'background-color': '#8b5cf6',
        shape: 'rectangle',
      },
    },
    {
      selector: 'node[risk > 70]',
      style: {
        'background-color': '#ef4444',
        'border-width': 3,
        'border-color': '#fca5a5',
      },
    },
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#4b5563',
        'target-arrow-color': '#4b5563',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        label: 'data(label)',
        'font-size': '8px',
        color: '#9ca3af',
      },
    },
  ];

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-4 overflow-hidden relative">
      <div className="flex items-center justify-between mb-3 text-xs text-gray-400">
        <span>Nodes: {graphData.nodes.length} | Edges: {graphData.edges.length}</span>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> IP Node
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-purple-500 inline-block"></span> Wallet Node
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> High Risk Node
          </span>
        </div>
      </div>

      <CytoscapeComponent
        elements={elements}
        style={{ width: '100%', height: '500px' }}
        stylesheet={stylesheet}
        layout={{ name: 'cose', animate: false }}
      />
    </div>
  );
};
