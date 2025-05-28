import { useQuery } from '@tanstack/react-query';
import {
  fetchBidHistory,
  fetchBidLogEntry,
  FilterState,
  PaginatedBidHistoryResponse,
  BidLogEntry,
} from '@/services/bidHistoryService';
import { bidHistoryKeys } from '@/lib/queryKeys';

const ITEMS_PER_PAGE = 10; // Default items per page, can be made configurable

// Hook to fetch paginated and filtered bid history
export function useBidHistory(filters: FilterState, page: number, limit: number = ITEMS_PER_PAGE) {
  return useQuery<PaginatedBidHistoryResponse, Error>({
    // Query key includes filters and pagination parameters to ensure uniqueness
    queryKey: bidHistoryKeys.list(filters, page, limit),
    queryFn: () => fetchBidHistory(filters, page, limit),
    // keepPreviousData is now a TanStack Query v5 default behavior
    // For older versions, you would set: keepPreviousData: true,
    // TanStack Query v5 handles this by default, so no explicit keepPreviousData is needed
    // to achieve the "lagged" data effect during refetches.
    // If you want to ensure data is not cleared while new data is loading,
    // and you are on v4 or want to be explicit:
    // placeholderData: (previousData) => previousData, // or keepPreviousData:true
    // In v5, this is generally handled well by default.
  });
}

// Hook to fetch a single bid log entry by ID
export function useBidLogEntry(entryId: string | undefined) { // Allow undefined entryId
  return useQuery<BidLogEntry, Error>({
    queryKey: bidHistoryKeys.detail(entryId!), // The ! assumes entryId will be defined when enabled
    queryFn: () => fetchBidLogEntry(entryId!),
    enabled: !!entryId, // Only run query if entryId is truthy
  });
}
