import { apiClient } from './apiClient';

export interface IngestResponse {
  status: string;
  filename: string;
  processed_records: number;
  generated_alerts_count: number;
  message: string;
}

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
