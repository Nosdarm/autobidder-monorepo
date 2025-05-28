// frontend-app/src/services/bidHistoryService.ts
import { format, subDays, addDays, parseISO, isWithinInterval } from 'date-fns';
import type { DateRange } from 'react-day-picker';

// --- Interfaces ---
export type BidStatus = "submitted" | "successful" | "failed" | "viewed" | "pending_review";

export interface BidLogEntry {
  id: string;
  profileId: string;
  profileName: string;
  vacancyId: string;
  submittedAt: Date; // Use Date objects internally, convert to/from string for storage/API
  responseAt?: Date;
  status: BidStatus;
  score?: number;
  apiResponse?: Record<string, any>;
}

export interface FilterState {
  profileId?: string | null;
  dateRange?: DateRange | undefined;
  statuses?: BidStatus[];
}

export interface PaginatedBidHistoryResponse {
  logs: BidLogEntry[];
  totalCount: number;
  totalPages: number;
}

// --- Mock Data Store & Helpers ---
const mockProfilesForService = [
  { id: 'profile1', name: 'My Main Upwork Profile' },
  { id: 'profile2', name: 'Agency Client - Tech Lead Roles' },
  { id: 'profile3', name: 'Side Gig - Quick Projects' },
];
const allStatusesForService: BidStatus[] = ["submitted", "successful", "failed", "viewed", "pending_review"];

let mockAllBidLogsDB: BidLogEntry[] = [];

const generateInitialMockBidLogs = (count: number): void => {
  const logs: BidLogEntry[] = [];
  for (let i = 1; i <= count; i++) {
    const profile = mockProfilesForService[i % mockProfilesForService.length];
    const submittedAt = subDays(new Date(), Math.floor(Math.random() * 180)); // Submitted in last 180 days
    let responseAt: Date | undefined;
    const status = allStatusesForService[Math.floor(Math.random() * allStatusesForService.length)];
    if (status !== "submitted" && status !== "pending_review") {
      responseAt = addDays(submittedAt, Math.floor(Math.random() * 14) + 1);
    }
    const score = status === "successful" ? Math.floor(Math.random() * 30) + 70 : (status === "failed" ? Math.floor(Math.random() * 40) : undefined);
    
    logs.push({
      id: `bid${i}`,
      profileId: profile.id,
      profileName: profile.name,
      vacancyId: `vac${1000 + i}`,
      submittedAt,
      responseAt,
      status,
      score,
      apiResponse: {
        success: status === "successful" || status === "submitted" || status === "viewed",
        message: `Bid status: ${status}`,
        timestamp: new Date().toISOString(),
        details: { attemptedBidId: `bid-attempt-${i}`, ...(score && { calculatedMatchScore: score }) },
      },
    });
  }
  mockAllBidLogsDB = logs.sort((a,b) => b.submittedAt.getTime() - a.submittedAt.getTime());
};

// Initialize DB
generateInitialMockBidLogs(150); // Generate a larger set for better pagination/filtering demo

const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// --- API Service Functions ---

export const fetchBidHistory = async (
  filters: FilterState,
  page: number,
  limit: number
): Promise<PaginatedBidHistoryResponse> => {
  await simulateDelay();
  console.log("API: Fetching bid history with filters:", filters, "page:", page, "limit:", limit);

  let filteredLogs = [...mockAllBidLogsDB];

  // Apply profile filter
  if (filters.profileId) {
    filteredLogs = filteredLogs.filter(log => log.profileId === filters.profileId);
  }

  // Apply date range filter
  if (filters.dateRange?.from) {
    const fromDate = filters.dateRange.from;
    if (filters.dateRange.to) {
      const toDate = addDays(filters.dateRange.to, 1); // Include the whole 'to' day
      filteredLogs = filteredLogs.filter(log => 
        isWithinInterval(log.submittedAt, { start: fromDate, end: toDate })
      );
    } else {
      filteredLogs = filteredLogs.filter(log => log.submittedAt >= fromDate);
    }
  }

  // Apply status filter
  if (filters.statuses && filters.statuses.length > 0) {
    filteredLogs = filteredLogs.filter(log => filters.statuses!.includes(log.status));
  }

  const totalCount = filteredLogs.length;
  const totalPages = Math.ceil(totalCount / limit);
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const logsForPage = filteredLogs.slice(startIndex, endIndex);

  console.log(`API: Returning ${logsForPage.length} logs for page ${page}. Total matching: ${totalCount}`);
  return {
    logs: logsForPage,
    totalCount,
    totalPages,
  };
};

export const fetchBidLogEntry = async (id: string): Promise<BidLogEntry> => {
  await simulateDelay();
  console.log(`API: Fetching bid log entry with id ${id}`);
  const logEntry = mockAllBidLogsDB.find(log => log.id === id);
  if (!logEntry) {
    throw new Error(`Bid log entry with id ${id} not found`);
  }
  return logEntry;
};
