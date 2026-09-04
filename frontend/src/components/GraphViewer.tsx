import React, { useCallback, useRef, useState } from 'react';
import cytoscape, { Core, NodeSingular, Stylesheet } from 'cytoscape';
import CytoscapeComponent from 'react-cytoscapejs';
import { Search, RotateCcw } from 'lucide-react';
import { CytoscapeGraphResponse } from '../services/api';

interface GraphViewerProps {
  graphData: CytoscapeGraphResponse | null;
}

const LAYOUTS: Record<string, cytoscape.LayoutOptions> = {
  cose: { name: 'cose', animate: true, padding: 40 } as cytoscape.LayoutOptions,
  breadthfirst: { name: 'breadthfirst', animate: true, padding: 40 } as cytoscape.LayoutOptions,
  concentric: {
    name: 'concentric',
    animate: true,
    padding: 40,
    concentric: (n: NodeSingular) => n.data('risk') || 0,
    levelWidth: () => 20,
  } as unknown as cytoscape.LayoutOptions,
};

export const GraphViewer: React.FC<GraphViewerProps> = ({ graphData }) => {
  const cyRef = useRef<Core | null>(null);
  const [selected, setSelected] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [layoutName, setLayoutName] = useState<keyof typeof LAYOUTS>('cose');

  const focusNode = useCallback((node: NodeSingular) => {
    const cy = cyRef.current;
    if (!cy) return;
    const neighborhood = node.closedNeighborhood();
    cy.elements().removeClass('highlighted').addClass('dimmed');
    neighborhood.removeClass('dimmed').addClass('highlighted');
    cy.animate({ center: { eles: node }, zoom: 1.4 }, { duration: 350 });
    setSelected(node.data());
  }, []);

  const clearFocus = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass('dimmed').removeClass('highlighted');
    setSelected(null);
  }, []);

  const handleCyInit = useCallback(
    (cy: Core) => {
      cyRef.current = cy;
      cy.off('tap');
      cy.on('tap', 'node', (evt) => focusNode(evt.target));
      cy.on('tap', (evt) => {
        if (evt.target === cy) clearFocus();
      });
    },
    [focusNode, clearFocus]
  );

  const runLayout = (name: keyof typeof LAYOUTS) => {
    setLayoutName(name);
    cyRef.current?.layout(LAYOUTS[name]).run();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const cy = cyRef.current;
    if (!cy || !query.trim()) return;
    const match = cy
      .nodes()
      .filter(
        (n) =>
          (n.data('label') || '').toLowerCase().includes(query.toLowerCase()) ||
          (n.data('id') || '').toLowerCase().includes(query.toLowerCase())
      )
      .first();
    if (match && match.length) focusNode(match);
  };

  if (!graphData) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-900 rounded-xl border border-gray-800 text-gray-500">
        Loading Cytoscape network graph...
      </div>
    );
  }

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

  const stylesheet: Stylesheet[] = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'background-color': '#3b82f6',
        color: '#ffffff',
        'font-size': '10px',
        'text-valign': 'bottom',
        'text-margin-y': 4,
        width: (ele: any) => 18 + Math.min(30, (ele.data('risk') || 0) * 0.3),
        height: (ele: any) => 18 + Math.min(30, (ele.data('risk') || 0) * 0.3),
      },
    },
    { selector: 'node[type = "ip"]', style: { 'background-color': '#10b981', shape: 'ellipse' } },
    { selector: 'node[type = "wallet"]', style: { 'background-color': '#8b5cf6', shape: 'rectangle' } },
    { selector: 'node[type = "tx"]', style: { 'background-color': '#6b7280', shape: 'diamond', width: 12, height: 12 } },
    {
      selector: 'node[risk > 70]',
      style: { 'background-color': '#ef4444', 'border-width': 3, 'border-color': '#fca5a5' },
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
    { selector: '.dimmed', style: { opacity: 0.12 } },
    { selector: '.highlighted', style: { 'border-width': 3, 'border-color': '#fbbf24', 'z-index': 999 } },
    { selector: 'edge.highlighted', style: { 'line-color': '#fbbf24', 'target-arrow-color': '#fbbf24', width: 3 } },
  ];

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-700 p-4 overflow-hidden relative">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <span className="text-xs text-gray-400">
          Nodes: {graphData.nodes.length} | Edges: {graphData.edges.length}
        </span>

        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="flex items-center bg-gray-800 border border-gray-700 rounded px-2 py-1">
            <Search className="h-3.5 w-3.5 text-gray-500 mr-1" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Find wallet / IP / TXID"
              className="bg-transparent text-xs text-gray-200 focus:outline-none w-40"
            />
          </div>
          <button
            type="submit"
            className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white"
          >
            Go
          </button>
        </form>

        <div className="flex items-center gap-1">
          {(Object.keys(LAYOUTS) as Array<keyof typeof LAYOUTS>).map((name) => (
            <button
              key={name}
              onClick={() => runLayout(name)}
              className={`text-xs px-2 py-1 rounded border ${
                layoutName === name
                  ? 'bg-amber-500 border-amber-500 text-gray-900 font-semibold'
                  : 'bg-gray-800 border-gray-700 text-gray-300'
              }`}
            >
              {name}
            </button>
          ))}
          <button
            onClick={clearFocus}
            className="text-xs px-2 py-1 rounded border border-gray-700 bg-gray-800 text-gray-300 flex items-center gap-1"
          >
            <RotateCcw className="h-3 w-3" /> Reset
          </button>
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> IP
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-purple-500 inline-block"></span> Wallet
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> High Risk
          </span>
        </div>
      </div>

      <div className="relative">
        <CytoscapeComponent
          elements={elements}
          style={{ width: '100%', height: '500px' }}
          stylesheet={stylesheet}
          layout={LAYOUTS[layoutName]}
          cy={handleCyInit}
        />

        {selected && (
          <div className="absolute top-3 right-3 w-64 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-xl">
            <button
              onClick={clearFocus}
              className="absolute top-2 right-2 text-gray-500 hover:text-gray-300 text-lg leading-none"
            >
              ×
            </button>
            <div className="text-[10px] font-bold text-blue-400 tracking-wider uppercase">
              {selected.type}
            </div>
            <div className="text-sm font-semibold text-white mt-1 mb-2 break-all">
              {selected.label}
            </div>
            <div className="text-xs text-gray-300 mb-3">
              Risk score:{' '}
              <b className={selected.risk >= 70 ? 'text-red-400' : selected.risk >= 35 ? 'text-amber-400' : 'text-gray-400'}>
                {selected.risk ?? '—'}
              </b>
            </div>
            <div className="text-[11px] text-gray-500 italic border-t border-gray-700 pt-2">
              SHAP evidence will render here once wired to the alert detail endpoint.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};