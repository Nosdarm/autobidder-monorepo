import { useQuery } from '@tanstack/react-query';
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
export function useIndividualDashboardStats() {
  return useQuery<IndividualDashboardStats, Error>({
    queryKey: dashboardKeys.individualStats(),
    queryFn: getIndividualDashboardStats,
    // staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Hook to fetch agency dashboard statistics
export function useAgencyDashboardStats() {
  return useQuery<AgencyDashboardStats, Error>({
    queryKey: dashboardKeys.agencyStats(),
    queryFn: getAgencyDashboardStats,
    // staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
