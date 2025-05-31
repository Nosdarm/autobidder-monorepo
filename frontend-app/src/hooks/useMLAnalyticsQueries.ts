import { useQuery } from '@tanstack/react-query';
import type { DateRange } from 'react-day-picker';
import {
  fetchMetricsCardsData,
  fetchLineChartData,
  fetchBarChartData,
  fetchJobsWithScores, // Added
  MetricCardData,
  ChartDataPoint,
  Job as JobData, // Added Job interface
} from '@/services/mlAnalyticsService';
import { mlAnalyticsKeys } from '@/lib/queryKeys';

// Helper to create a stable query key from the dateRange object
const createDateRangeKey = (dateRange?: DateRange) => ({
  from: dateRange?.from?.toISOString(),
  to: dateRange?.to?.toISOString(),
});

// Hook to fetch metrics cards data
export function useMLMetricsCards(dateRange?: DateRange) {
  const stableDateRangeKey = createDateRangeKey(dateRange);
  return useQuery<MetricCardData[], Error>({
    queryKey: mlAnalyticsKeys.metrics(stableDateRangeKey),
    queryFn: () => fetchMetricsCardsData(dateRange),
    // keepPreviousData: true, // TanStack Query v5 default behavior
  });
}

// Hook to fetch line chart data
export function useMLLineChartData(dateRange?: DateRange) {
  const stableDateRangeKey = createDateRangeKey(dateRange);
  return useQuery<ChartDataPoint[], Error>({
    queryKey: mlAnalyticsKeys.lineChart(stableDateRangeKey),
    queryFn: () => fetchLineChartData(dateRange),
    // keepPreviousData: true,
  });
}

// Hook to fetch jobs with scores data
export function useMLJobsWithScores(dateRange?: DateRange) {
  const stableDateRangeKey = createDateRangeKey(dateRange);
  return useQuery<JobData[], Error>({ // Use JobData interface
    queryKey: mlAnalyticsKeys.jobsWithScores(stableDateRangeKey),
    queryFn: () => fetchJobsWithScores(dateRange),
    // keepPreviousData: true,
  });
}

// Hook to fetch bar chart data
export function useMLBarChartData(dateRange?: DateRange) {
  const stableDateRangeKey = createDateRangeKey(dateRange);
  return useQuery<ChartDataPoint[], Error>({
    queryKey: mlAnalyticsKeys.barChart(stableDateRangeKey),
    queryFn: () => fetchBarChartData(dateRange),
    // keepPreviousData: true,
  });
}
