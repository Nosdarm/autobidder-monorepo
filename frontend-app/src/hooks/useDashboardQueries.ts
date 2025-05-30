import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import {
  fetchDashboardSummaryStats,
  DashboardSummaryStats,
  getIndividualDashboardStats,
  IndividualDashboardStats,
  getAgencyDashboardStats,
  AgencyDashboardStats,
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

// Hook to fetch individual dashboard statistics
export function useIndividualDashboardStats(options?: Omit<UseQueryOptions<IndividualDashboardStats, Error, IndividualDashboardStats, ReturnType<typeof dashboardKeys.individualStats>>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: dashboardKeys.individualStats(),
    queryFn: getIndividualDashboardStats,
    // staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
}

// Hook to fetch agency dashboard statistics
export function useAgencyDashboardStats(options?: Omit<UseQueryOptions<AgencyDashboardStats, Error, AgencyDashboardStats, ReturnType<typeof dashboardKeys.agencyStats>>, 'queryKey' | 'queryFn'>) {
  return useQuery({
    queryKey: dashboardKeys.agencyStats(),
    queryFn: getAgencyDashboardStats,
    // staleTime: 5 * 60 * 1000, // 5 minutes
    ...options
  });
}
