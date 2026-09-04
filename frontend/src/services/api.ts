import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AlertData {
  entity_type: 'wallet' | 'ip';
  entity_id: string;
  risk_score: number;
  confidence: number;
  reason: string;
  shap_explanation: Record<string, number>;
}

export interface PaginatedAlertResponse {
  total: number;
  page: number;
  limit: number;
  alerts: AlertData[];
}

export interface DashboardStats {
  total_transactions_ingested?: number;
  total_entities_monitored?: number;
  high_risk_alerts_count?: number;
  medium_risk_alerts_count?: number;
  active_peers_count?: number;
  critical_threat_entities?: number;
  total_alerts?: number;
  critical_alerts?: number;
  anomalous_volume_btc?: number;
  dominant_pattern?: string;
  risk_score_distribution?: Record<string, number>;
  top_flagged_countries?: Array<{ country: string; flagged_count: number }>;
}

export interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    type: string;
    risk_score?: number;
  };
}

export interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    label?: string;
    amount?: number;
  };
}

export interface CytoscapeGraphResponse {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
}

export interface IngestResponse {
  status: string;
  filename: string;
  processed_records: number;
  generated_alerts_count: number;
  message: string;
}

export interface SearchResultItem {
  entity_type: string;
  entity_id: string;
  risk_score: number;
  summary: string;
}

export interface SearchResponse {
  query: string;
  results_count: number;
  results: SearchResultItem[];
}

// API Endpoint Bindings
export const fetchAlerts = async (
  page = 1,
  limit = 10,
  minScore = 0.0,
  entityType?: string
): Promise<PaginatedAlertResponse> => {
  const response = await apiClient.get<PaginatedAlertResponse>('/api/v1/alerts', {
    params: { page, limit, min_score: minScore, entity_type: entityType },
  });
  return response.data;
};

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/api/v1/dashboard/stats');
  return response.data;
};

export const clearAlerts = async (): Promise<{ status: string; message: string; cleared_count: number }> => {
  const response = await apiClient.post('/api/v1/alerts/clear');
  return response.data;
};

export const fetchNetworkGraph = async (
  entityId?: string,
  depth = 2
): Promise<CytoscapeGraphResponse> => {
  const response = await apiClient.get<CytoscapeGraphResponse>('/api/v1/graph', {
    params: { entity_id: entityId, depth },
  });
  return response.data;
};

export const uploadTrafficFile = async (file: File): Promise<IngestResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<IngestResponse>('/api/v1/ingest', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const globalSearch = async (query: string): Promise<SearchResponse> => {
  const response = await apiClient.get<SearchResponse>('/api/v1/search', {
    params: { q: query },
  });
  return response.data;
};
