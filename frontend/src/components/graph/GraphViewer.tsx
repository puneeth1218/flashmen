import React, { useCallback, useRef, useState } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import CytoscapeComponent from 'react-cytoscapejs';
import { Search, RotateCcw } from 'lucide-react';
import { CytoscapeGraphResponse, fetchAlerts, AlertData } from '../../services/api';

interface GraphViewerProps {
  graphData: CytoscapeGraphResponse | null;
}

const LAYOUTS: Record<string, cytoscape.LayoutOptions> = {
  cose: {
    name: 'cose',
    animate: true,
    idealEdgeLength: 100,
    nodeOverlap: 20,
    refresh: 20,
    fit: true,
    padding: 30,
    randomize: false,
    componentSpacing: 100,
    nodeRepulsion: 400000,
    edgeElasticity: 100,
    nestingFactor: 5,
    gravity: 80,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
  } as unknown as cytoscape.LayoutOptions,
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
  const [alertDetail, setAlertDetail] = useState<AlertData | null>(null);
  const [loadingAlert, setLoadingAlert] = useState(false);

  const focusNode = useCallback((node: NodeSingular) => {
    const cy = cyRef.current;
    if (!cy) return;
    const neighborhood = node.closedNeighborhood();
    cy.elements().removeClass('highlighted').addClass('dimmed');
    neighborhood.removeClass('dimmed').addClass('highlighted');
    cy.animate({ center: { eles: node }, zoom: 1.4 }, { duration: 350 });
    setSelected(node.data());

    // Look up this entity's SHAP explanation from the alerts endpoint
    const entityId = node.data('id');
    setLoadingAlert(true);
    setAlertDetail(null);
    fetchAlerts(1, 100)
      .then((res) => {
        const alertsList = Array.isArray(res) ? res : ((res as any)?.alerts || []);
        const match = alertsList.find((a: AlertData) => a.entity_id === entityId);
        setAlertDetail(match ?? null);
      })
      .catch((err) => {
        console.error('Failed to fetch alert detail:', err);
      })
      .finally(() => {
        setLoadingAlert(false);
      });
  }, []);

  const clearFocus = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass('dimmed').removeClass('highlighted');
    setSelected(null);
    setAlertDetail(null);
  }, []);

  const handleCyInit = useCallback(
    (cy: Core) => {
      cyRef.current = cy;
      cy.off('tap');
      cy.on('tap', 'node', (evt) => {
        if (evt.target.isNode()) {
          focusNode(evt.target);
        }
      });
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
    if (match && match.length && match.isNode()) {
      focusNode(match);
    }
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
        pattern_tag: node.data.pattern_tag || '',
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

  const stylesheet = [
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
    { selector: 'node[type = "tx"]', style: { 'background-color': '#6b7280', shape: 'diamond', width: 14, height: 14 } },
    {
      selector: 'node[risk > 70]',
      style: { 'background-color': '#ef4444', 'border-width': 3, 'border-color': '#fca5a5' },
    },
    {
      selector: 'node[pattern_tag = "Peel Chain"]',
      style: { 'border-width': 2.5, 'border-color': '#f59e0b', 'background-color': '#d97706' },
    },
    {
      selector: 'node[pattern_tag = "Mixer"]',
      style: { 'border-width': 2.5, 'border-color': '#ec4899', 'background-color': '#db2777' },
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
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-amber-500 inline-block"></span> Peel Chain
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-pink-500 inline-block"></span> Mixer
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
          <div className="absolute top-3 right-3 w-72 bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-xl z-20">
            <button
              onClick={clearFocus}
              className="absolute top-2 right-2 text-gray-500 hover:text-gray-300 text-lg leading-none"
            >
              ×
            </button>
            <div className="flex items-center justify-between gap-2">
              <div className="text-[10px] font-bold text-blue-400 tracking-wider uppercase">
                {selected.type}
              </div>
              {selected.pattern_tag && (
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                  selected.pattern_tag === 'Mixer'
                    ? 'bg-pink-900/60 text-pink-300 border-pink-700'
                    : selected.pattern_tag === 'Peel Chain'
                    ? 'bg-amber-900/60 text-amber-300 border-amber-700'
                    : 'bg-red-900/60 text-red-300 border-red-700'
                }`}>
                  {selected.pattern_tag}
                </span>
              )}
            </div>
            <div className="text-sm font-semibold text-white mt-1 mb-2 break-all">
              {selected.label}
            </div>
            <div className="text-xs text-gray-300 mb-1">
              Risk score:{' '}
              <b className={(alertDetail ? alertDetail.risk_score : selected.risk) >= 70 ? 'text-red-400' : (alertDetail ? alertDetail.risk_score : selected.risk) >= 35 ? 'text-amber-400' : 'text-gray-400'}>
                {alertDetail ? alertDetail.risk_score : (selected.risk ?? '—')}
              </b>
            </div>
            {alertDetail && (
              <div className="text-xs text-gray-300 mb-2">
                Confidence:{' '}
                <b className="text-blue-400">
                  {Math.round(alertDetail.confidence * 100)}%
                </b>
              </div>
            )}
            <div className="text-[11px] text-gray-400 border-t border-gray-700 pt-2">
              {loadingAlert ? (
                <span className="italic text-gray-500">Loading explanation…</span>
              ) : alertDetail ? (
                <>
                  <div className="mb-1 text-gray-200">
                    <span className="font-semibold text-gray-400">Primary Reason:</span> {alertDetail.reason}
                  </div>
                  {Object.keys(alertDetail.shap_explanation ?? {}).length > 0 && (
                    <ul className="mt-1 space-y-0.5 text-gray-400">
                      {Object.entries(alertDetail.shap_explanation)
                        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                        .slice(0, 3)
                        .map(([feature, contribution]) => (
                          <li key={feature}>
                            {feature}: {contribution > 0 ? '+' : ''}
                            {contribution.toFixed(1)}
                          </li>
                        ))}
                    </ul>
                  )}
                </>
              ) : (
                <span className="italic text-gray-500">No alert record found for this entity.</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};