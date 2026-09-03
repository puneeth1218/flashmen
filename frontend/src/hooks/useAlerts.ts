import { useQuery } from '@tanstack/react-query';
import { fetchAlerts, AlertData } from '../services/api/alerts';

export const useAlerts = () => {
  return useQuery<AlertData[], Error>({
    queryKey: ['alerts'],
    queryFn: fetchAlerts,
  });
};
