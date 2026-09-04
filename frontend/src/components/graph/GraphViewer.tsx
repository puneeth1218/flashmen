import { useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { Core, NodeSingular } from 'cytoscape';
import { CytoscapeGraphResponse } from '../../services/api';
import { mockGraphData } from './mockData';
import NodeDetailPanel from './NodeDetailPanel';
import './GraphViewer.css';

interface Props {
  graphData?: CytoscapeGraphResponse | null;
}

const layout = { name: 'cose', animate: true };

const stylesheet: any[] =  [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      'background-color': (ele: NodeSingular) => {
        const score = ele.data('risk_score') ?? 0;
        if (score >= 70) return '#e04b4b';
        if (score >= 40) return '#e0a94b';
        return '#4b9be0';
      },
      color: '#fff',
      'font-size': 10,
      width: 32,
      height: 32,
      'text-valign': 'top',
      'text-halign': 'center',
      'text-margin-y': -6,
      'text-outline-width': 2,
      'text-outline-color': '#000',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#888',
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#888',
      label: 'data(label)',
      'font-size': 8,
      color: '#aaa',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#fff',
    },
  },
];

export default function GraphViewer({ graphData }: Props) {
  const data = graphData ?? mockGraphData;
  const [selectedNode, setSelectedNode] = useState<{
    id: string;
    label: string;
    type: string;
    riskScore: number;
  } | null>(null);

  const elements = [...(data.nodes ?? []), ...(data.edges ?? [])];

  const handleReady = (cy: Core) => {
    cy.removeAllListeners();
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.data('id'),
        label: node.data('label') ?? node.data('id'),
        type: node.data('type') ?? 'unknown',
        riskScore: node.data('risk_score') ?? 0,
      });
    });
    cy.on('tap', (evt) => {
      if (evt.target === cy) setSelectedNode(null);
    });
  };

  return (
    <div className="graph-viewer">
      <CytoscapeComponent
        elements={CytoscapeComponent.normalizeElements(elements)}
        style={{ width: '100%', height: '600px' }}
        layout={layout}
        stylesheet={stylesheet}
        cy={handleReady}
      />
      {selectedNode && (
        <NodeDetailPanel
          nodeId={selectedNode.id}
          label={selectedNode.label}
          entityType={selectedNode.type}
          riskScore={selectedNode.riskScore}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}