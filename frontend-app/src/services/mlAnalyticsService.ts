// frontend-app/src/services/mlAnalyticsService.ts
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
  // raw_data?: any; // If needed
  // description_embedding?: number[]; // If needed
  predicted_score?: number; // New field
}

export interface MetricCardData {
  title: string;
  value: string;
  // Icon name or component can be handled in the UI layer based on title
}

export interface ChartDataPoint {
  name: string; // X-axis label (e.g., date, feature name)
  value: number; // Y-axis value
}

const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// --- API Service Functions ---

// Mock function to fetch jobs with predicted scores
export const fetchJobsWithScores = async (dateRange?: DateRange): Promise<Job[]> => {
  await simulateDelay(600);
  console.log("API: Fetching jobs with scores for date range:", dateRange);
  // Simulate some jobs, some with scores, some without
  const mockJobs: Job[] = [
    { id: "1", title: "Develop AI-Powered Chatbot", description: "Need a chatbot for customer service.", posted_time: subDays(new Date(), 2).toISOString(), predicted_score: 85.5, upwork_job_id: "up_j1" },
    { id: "2", title: "Create Data Visualization Dashboard", description: "Dashboard for sales data.", posted_time: subDays(new Date(), 5).toISOString(), predicted_score: 72.1, upwork_job_id: "up_j2" },
    { id: "3", title: "Migrate Database to Cloud", description: "Migrate existing SQL Server to Azure.", posted_time: subDays(new Date(), 1).toISOString(), predicted_score: undefined, upwork_job_id: "up_j3" },
    { id: "4", title: "SEO Optimization for E-commerce Site", description: "Improve search rankings.", posted_time: subDays(new Date(), 10).toISOString(), predicted_score: 91.0, upwork_job_id: "up_j4" },
    { id: "5", title: "Write Technical Documentation", description: "Document our new API.", posted_time: subDays(new Date(), 3).toISOString(), predicted_score: null as any, upwork_job_id: "up_j5" }, // Test null explicitly
  ];
  // Simulate date range filtering very crudely
  if (dateRange?.from) {
    return mockJobs.filter(job => job.posted_time && new Date(job.posted_time) >= dateRange.from!);
  }
  return mockJobs;
};

// Helper to generate a value that slightly changes based on date range
const generateDynamicValue = (base: number, dateRange?: DateRange): number => {
  let factor = 1;
  if (dateRange?.from && dateRange?.to) {
    const days = differenceInDays(dateRange.to, dateRange.from);
    factor = 1 + (days % 10) * 0.01; // Change by up to 10% based on day span
  } else if (dateRange?.from) {
    factor = 1 + (dateRange.from.getDate() % 5) * 0.01; // Change by up to 5% based on from date
  }
  return parseFloat((base * factor).toFixed(2));
};

// Helper to add days, used in one of the charts, ensure it's available if it was missing.
// Not strictly needed for job scores but part of existing file context.
const addDays = (date: Date, days: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

export const fetchMetricsCardsData = async (dateRange?: DateRange): Promise<MetricCardData[]> => {
  await simulateDelay(300);
  console.log("API: Fetching metrics cards data for date range:", dateRange);
  // Simulate data changing based on date range
  return [
    { title: "Precision@k", value: `${generateDynamicValue(85.3, dateRange).toFixed(1)}%` },
    { title: "Recall@k", value: `${generateDynamicValue(78.9, dateRange).toFixed(1)}%` },
    { title: "F1 Score", value: `${generateDynamicValue(0.82, dateRange).toFixed(2)}` },
    { title: "Overall Accuracy", value: `${generateDynamicValue(92.1, dateRange).toFixed(1)}%` },
  ];
};

export const fetchLineChartData = async (dateRange?: DateRange): Promise<ChartDataPoint[]> => {
  await simulateDelay(700);
  console.log("API: Fetching line chart data for date range:", dateRange);

  const from = dateRange?.from || subDays(new Date(), 6);
  const to = dateRange?.to || new Date();
  const interval = eachDayOfInterval({ start: from, end: to });

  // Ensure a minimum number of data points if the interval is too short
  if (interval.length < 2 && interval.length > 0) {
    interval.push(addDays(interval[0], 1)); // Add a second day if only one
  } else if (interval.length === 0) { // Handle case where from and to might be same day, or invalid
      interval.push(subDays(new Date(),1));
      interval.push(new Date());
  }


  return interval.map((day, index) => ({
    name: format(day, 'MMM d'),
    value: parseFloat((0.75 + Math.sin(index + (day.getDate()/5)) * 0.05 + generateDynamicValue(0, dateRange) * 0.01).toFixed(2)), // Sin wave + date factor
  }));
};

export const fetchBarChartData = async (dateRange?: DateRange): Promise<ChartDataPoint[]> => {
  await simulateDelay(500);
  console.log("API: Fetching bar chart data for date range:", dateRange);
  // Feature importance might not change as frequently with date range,
  // but we can add a slight variation.
  return [
    { name: "Keyword Match", value: generateDynamicValue(45, dateRange) },
    { name: "Historical Success", value: generateDynamicValue(30, dateRange) },
    { name: "Profile Completeness", value: generateDynamicValue(15, dateRange) },
    { name: "Bid Amount Strategy", value: generateDynamicValue(10, dateRange) },
  ].sort((a,b) => b.value - a.value); // Sort by importance
};
