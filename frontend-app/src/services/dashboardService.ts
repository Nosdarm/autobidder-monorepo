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

// --- Interfaces for Differentiated Dashboards ---
export interface IndividualDashboardStats {
  averageBidSuccessRate: string; // e.g., "70%"
  // Potentially other individual-specific stats
}

export interface AgencyDashboardStats {
  managedClientProfilesCount: number;
  teamMembersCount: number;
  recentTeamBidsCount: number;
  clientSatisfactionScore: string; // e.g., "4.5/5 Stars"
  // Potentially other agency-specific stats
}

// --- API Service Functions for Differentiated Dashboards ---

export const getIndividualDashboardStats = async (): Promise<IndividualDashboardStats> => {
  await simulateDelay(400); // Simulate network delay
  console.log("API: Fetching individual dashboard stats");

  // Simulate potential error
  if (Math.random() < 0.05) { // 5% chance of error
    throw new Error("Failed to fetch individual dashboard statistics due to a simulated server error.");
  }

  return {
    averageBidSuccessRate: `${Math.floor(Math.random() * 30) + 60}%`, // Randomize between 60-90%
  };
};

export const getAgencyDashboardStats = async (): Promise<AgencyDashboardStats> => {
  await simulateDelay(700); // Simulate network delay
  console.log("API: Fetching agency dashboard stats");

  // Simulate potential error
  if (Math.random() < 0.08) { // 8% chance of error
    throw new Error("Failed to fetch agency dashboard statistics due to a simulated server error.");
  }
  
  // Derive managedClientProfilesCount from profileService's mock data for simplicity
  const managedClientProfilesCount = profilesFromProfileService.length + Math.floor(Math.random() * 10); // Example logic

  return {
    managedClientProfilesCount,
    teamMembersCount: Math.floor(Math.random() * 10) + 2, // 2-11 team members
    recentTeamBidsCount: Math.floor(Math.random() * 150) + 50, // 50-199 team bids
    clientSatisfactionScore: `${(Math.random() * 1.5 + 3.5).toFixed(1)}/5 Stars`, // Randomize between 3.5-5.0
  };
};
