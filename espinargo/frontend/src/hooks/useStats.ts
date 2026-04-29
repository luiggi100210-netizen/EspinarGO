import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { DashboardStats } from '@/types';

/**
 * Hook para obtener estadísticas del dashboard
 * Usa React Query para cache automático cada 30 segundos
 */
export function useStats() {
  const { data, isLoading, error, refetch } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/api/v1/stats/dashboard');
      return response.data;
    },
    refetchInterval: 30000,
    staleTime: 300000,
  });

  return {
    stats: data,
    isLoading,
    error,
    refetch,
  };
}