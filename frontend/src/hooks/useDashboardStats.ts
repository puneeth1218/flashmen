import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats, DashboardStats } from '../services/api/alerts';

export const useDashboardStats = () => {
  return useQuery<DashboardStats, Error>({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
  });
};
