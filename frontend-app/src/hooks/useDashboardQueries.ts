import { useQuery } from '@tanstack/react-query';
import {
  fetchDashboardSummaryStats,
  DashboardSummaryStats,
} from '@/services/dashboardService';
import { dashboardKeys } from '@/lib/queryKeys';

// Hook to fetch dashboard summary statistics
export function useDashboardSummaryStats() {
  return useQuery<DashboardSummaryStats, Error>({
    queryKey: dashboardKeys.summaryStats(),
    queryFn: fetchDashboardSummaryStats,
    // Consider adding staleTime if this data doesn't need to be ultra-fresh,
    // e.g., staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
