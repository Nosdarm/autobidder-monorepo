// frontend-app/src/services/mlAnalyticsService.ts
import apiClient from '@/lib/axios'; // Import the configured Axios instance
import { format, subDays, eachDayOfInterval, differenceInDays } from 'date-fns';
import type { DateRange } from 'react-day-picker';

// --- Interfaces ---
export interface Job {
  id: string;
  title: string;
  description?: string;
  upwork_job_id?: string;
  url?: string;
  posted_time?: string; // Consider Date object if manipulating
  predicted_score?: number; // New field
}

export interface MetricCardData {
  title: string;
  value: string;
}

export interface ChartDataPoint {
  name: string; // X-axis label (e.g., date, feature name)
  value: number; // Y-axis value
}

// Helper to simulate delay, can be removed if all functions become real
// const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Updated function to fetch REAL jobs with scores
export const fetchJobsWithScores = async (dateRange?: DateRange): Promise<Job[]> => {
  console.log("API (Real): Fetching jobs with scores for date range:", dateRange);

  const params: Record<string, string> = {};
  if (dateRange?.from) {
    // Format date as YYYY-MM-DD, standard for many backends
    params.startDate = format(dateRange.from, 'yyyy-MM-dd');
  }
  if (dateRange?.to) {
    params.endDate = format(dateRange.to, 'yyyy-MM-dd');
  }

  try {
    // Assuming the backend API for jobs is at /api/v1/jobs/
    // And it supports startDate and endDate query parameters.
    // If the API returns Job[] directly, no transformation is needed.
    const response = await apiClient.get<Job[]>('/api/v1/jobs/', { params });
    console.log("API (Real): Received jobs data:", response.data);
    return response.data;
  } catch (error) {
    console.error("API (Real): Error fetching jobs with scores:", error);
    // Propagate the error so react-query can handle it (e.g., set isError state)
    throw error;
  }
};


// Helper to generate a value that slightly changes based on date range (used by mock functions)
const generateDynamicValue = (base: number, dateRange?: DateRange): number => {
  let factor = 1;
  if (dateRange?.from && dateRange?.to) {
    const days = differenceInDays(dateRange.to, dateRange.from);
    factor = 1 + (days % 10) * 0.01;
  } else if (dateRange?.from) {
    factor = 1 + (dateRange.from.getDate() % 5) * 0.01;
  }
  return parseFloat((base * factor).toFixed(2));
};

// Helper to add days, used in one of the mock charts
const addDays = (date: Date, days: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

// --- Mock API Service Functions (Kept for other parts of MLAnalyticsPage) ---

export const fetchMetricsCardsData = async (dateRange?: DateRange): Promise<MetricCardData[]> => {
  await new Promise(resolve => setTimeout(resolve, 300)); // simulateDelay
  console.log("API (Mock): Fetching metrics cards data for date range:", dateRange);
  return [
    { title: "Precision@k", value: `${generateDynamicValue(85.3, dateRange).toFixed(1)}%` },
    { title: "Recall@k", value: `${generateDynamicValue(78.9, dateRange).toFixed(1)}%` },
    { title: "F1 Score", value: `${generateDynamicValue(0.82, dateRange).toFixed(2)}` },
    { title: "Overall Accuracy", value: `${generateDynamicValue(92.1, dateRange).toFixed(1)}%` },
  ];
};

export const fetchLineChartData = async (dateRange?: DateRange): Promise<ChartDataPoint[]> => {
  await new Promise(resolve => setTimeout(resolve, 700)); // simulateDelay
  console.log("API (Mock): Fetching line chart data for date range:", dateRange);

  const from = dateRange?.from || subDays(new Date(), 6);
  const to = dateRange?.to || new Date();
  const interval = eachDayOfInterval({ start: from, end: to });

  if (interval.length < 2 && interval.length > 0) {
    interval.push(addDays(interval[0], 1));
  } else if (interval.length === 0) {
      interval.push(subDays(new Date(),1));
      interval.push(new Date());
  }

  return interval.map((day, index) => ({
    name: format(day, 'MMM d'),
    value: parseFloat((0.75 + Math.sin(index + (day.getDate()/5)) * 0.05 + generateDynamicValue(0, dateRange) * 0.01).toFixed(2)),
  }));
};

export const fetchBarChartData = async (dateRange?: DateRange): Promise<ChartDataPoint[]> => {
  await new Promise(resolve => setTimeout(resolve, 500)); // simulateDelay
  console.log("API (Mock): Fetching bar chart data for date range:", dateRange);
  return [
    { name: "Keyword Match", value: generateDynamicValue(45, dateRange) },
    { name: "Historical Success", value: generateDynamicValue(30, dateRange) },
    { name: "Profile Completeness", value: generateDynamicValue(15, dateRange) },
    { name: "Bid Amount Strategy", value: generateDynamicValue(10, dateRange) },
  ].sort((a,b) => b.value - a.value);
};
