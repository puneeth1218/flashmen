import { apiClient } from './apiClient';

export interface AlertData {
  entity_type: 'wallet' | 'ip';
  entity_id: string;
  risk_score: number;
  confidence: number;
  reason: string;
  shap_explanation: Record<string, number>;
}

export interface DashboardStats {
  total_alerts?: number;
  critical_alerts?: number;
  active_entities?: number;
  [key: string]: any;
}

export const fetchAlerts = async (): Promise<AlertData[]> => {
  const response = await apiClient.get<AlertData[]>('/api/v1/alerts');
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
