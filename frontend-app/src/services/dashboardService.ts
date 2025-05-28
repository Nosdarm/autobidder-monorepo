// frontend-app/src/services/dashboardService.ts

// Attempt to import mockProfilesDB directly for count.
// This is a simplification for the mock environment.
// In a real app, activeProfilesCount would come from its own API endpoint or be part of a larger dashboard API response.
import { mockProfilesDB as profilesFromProfileService } from './profileService'; // Adjust path as needed

// --- Interfaces ---
export type AutobidJobStatus = 'active' | 'inactive' | 'error';

export interface DashboardSummaryStats {
  activeProfilesCount: number;
  runningAutobidJobsCount: number;
  runningAutobidJobsStatus: AutobidJobStatus;
  recentBidsCount: number;
}

const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// --- API Service Functions ---
export const fetchDashboardSummaryStats = async (): Promise<DashboardSummaryStats> => {
  await simulateDelay(600); // Simulate network delay
  console.log("API: Fetching dashboard summary stats");

  // Simulate potential error
  if (Math.random() < 0.1) { // 10% chance of error
    throw new Error("Failed to fetch dashboard summary statistics due to a simulated server error.");
  }

  // Derive activeProfilesCount from profileService's mock data
  // This assumes profileService.ts's mockProfilesDB is accessible and represents all profiles.
  // A more realistic scenario would involve an API call that calculates this on the backend.
  const activeProfilesCount = profilesFromProfileService.length;

  // Generate random numbers for other stats
  const runningAutobidJobsCount = Math.floor(Math.random() * 10); // 0-9 jobs
  const recentBidsCount = Math.floor(Math.random() * 100) + 50; // 50-149 bids

  let runningAutobidJobsStatus: AutobidJobStatus = 'inactive';
  if (runningAutobidJobsCount > 0) {
    const statusRoll = Math.random();
    if (statusRoll < 0.05) runningAutobidJobsStatus = 'error'; // 5% chance of error status
    else runningAutobidJobsStatus = 'active';
  }
  
  return {
    activeProfilesCount,
    runningAutobidJobsCount,
    runningAutobidJobsStatus,
    recentBidsCount,
  };
};
