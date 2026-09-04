import { CytoscapeGraphResponse } from '../../services/api';

export const mockGraphData: CytoscapeGraphResponse = {
  nodes: [
    { data: { id: 'wallet_1', label: 'Wallet A', type: 'wallet', risk_score: 92 } },
    { data: { id: 'wallet_2', label: 'Wallet B', type: 'wallet', risk_score: 34 } },
    { data: { id: 'wallet_3', label: 'Wallet C', type: 'wallet', risk_score: 78 } },
    { data: { id: 'ip_1', label: '192.168.1.10', type: 'ip', risk_score: 55 } },
    { data: { id: 'ip_2', label: '10.0.0.5', type: 'ip', risk_score: 12 } },
  ],
  edges: [
    { data: { id: 'e1', source: 'wallet_1', target: 'ip_1' } },
    { data: { id: 'e2', source: 'wallet_2', target: 'ip_1' } },
    { data: { id: 'e3', source: 'wallet_3', target: 'ip_2' } },
    { data: { id: 'e4', source: 'wallet_1', target: 'wallet_3' } },
  ],
};