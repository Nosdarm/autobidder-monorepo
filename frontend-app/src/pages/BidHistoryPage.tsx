import React, { useState, useEffect } from 'react'; // Added useEffect
import { format, subDays, addDays } from 'date-fns';
import { CalendarIcon, DownloadIcon, FilterIcon, XIcon, AlertTriangle } from 'lucide-react'; // Added AlertTriangle
import { useToast } from '@/hooks/useToast';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton'; // For loading state
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '@/components/ui/table';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; // Using Card for filter panel
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { DateRange } from 'react-day-picker';
import { Calendar } from "@/components/ui/calendar"; // shadcn/ui Calendar
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from '@/components/ui/badge';
import { useBidHistory } from '@/hooks/useBidHistoryQueries'; // Import the hook
import type { BidLogEntry, BidStatus, FilterState } from '@/services/bidHistoryService'; // Import types

// Mock Profile Data for Select - This can be fetched via React Query if needed in a real app
const mockProfilesForFilter = [
  { id: 'profile1', name: 'My Main Upwork Profile' },
  { id: 'profile2', name: 'Agency Client - Tech Lead Roles' },
  { id: 'profile3', name: 'Side Gig - Quick Projects' },
];

const allStatusesForFilter: BidStatus[] = ["submitted", "successful", "failed", "viewed", "pending_review"];

const ITEMS_PER_PAGE = 10;

export default function BidHistoryPage() {
  const { showToastSuccess } = useToast();
  
  const initialFilters: FilterState = {
    profileId: null,
    dateRange: undefined,
    statuses: [],
  };
  // This 'activeFilters' state is what's passed to the useBidHistory hook.
  // It's updated only when "Apply Filters" is clicked.
  const [activeFilters, setActiveFilters] = useState<FilterState>(initialFilters);
  
  // This 'draftFilters' state is for the form elements, updated on change.
  const [draftFilters, setDraftFilters] = useState<FilterState>(initialFilters);
  
  const [currentPage, setCurrentPage] = useState(1);

  const { 
    data: paginatedData, 
    isLoading, 
    isError, 
    error,
    isFetching, // Use isFetching for loading states during refetch/pagination
  } = useBidHistory(activeFilters, currentPage, ITEMS_PER_PAGE);

  const currentTableData = paginatedData?.logs || [];
  const totalPages = paginatedData?.totalPages || 0;

  const handleApplyFilters = () => {
    setActiveFilters(draftFilters); // This will trigger the useBidHistory hook to refetch
    setCurrentPage(1); 
  };

  const handleClearFilters = () => {
    setDraftFilters(initialFilters);
    setActiveFilters(initialFilters); // This will also trigger a refetch
    setCurrentPage(1);
  };

  const handleExportCSV = () => {
    showToastSuccess("CSV export functionality to be implemented.");
    // For export, you might want to fetch all data matching current filters,
    // not just the current page. This would be a separate API call or logic.
    console.log("Export CSV clicked. Current active filters:", activeFilters);
    console.log("Currently displayed data:", currentTableData);
  };
  
  const getStatusBadgeVariant = (status: BidStatus): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "successful": return "default"; // Often green
      case "submitted": return "secondary";
      case "pending_review": return "outline"; // Yellowish/Blueish
      case "viewed": return "outline";
      case "failed": return "destructive";
      default: return "secondary";
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Bid History & Logs</h1>
          <p className="text-muted-foreground">
            Review past bidding activities and their outcomes.
          </p>
        </div>
        <Button onClick={handleExportCSV} variant="outline">
          <DownloadIcon className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>

      <Collapsible className="space-y-4">
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="w-full sm:w-auto">
            <FilterIcon className="mr-2 h-4 w-4" /> Show Filters
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <Card className="p-6 shadow-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Profile Filter */}
              <div className="space-y-2">
                <Label htmlFor="profile-filter">Profile</Label>
                <Select 
                  value={draftFilters.profileId || ""}
                  onValueChange={(value) => setDraftFilters(prev => ({ ...prev, profileId: value === "all" ? null : value }))}
                >
                  <SelectTrigger id="profile-filter">
                    <SelectValue placeholder="All Profiles" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Profiles</SelectItem>
                    {mockProfilesForFilter.map(profile => ( // Use mockProfilesForFilter
                      <SelectItem key={profile.id} value={profile.id}>{profile.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Date Range Filter */}
              <div className="space-y-2">
                <Label htmlFor="date-range-filter">Date Range</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      id="date-range-filter"
                      variant={"outline"}
                      className={`w-full justify-start text-left font-normal ${!draftFilters.dateRange && "text-muted-foreground"}`}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {draftFilters.dateRange?.from ? (
                        draftFilters.dateRange.to ? (
                          <>
                            {format(draftFilters.dateRange.from, "LLL dd, y")} -{" "}
                            {format(draftFilters.dateRange.to, "LLL dd, y")}
                          </>
                        ) : (
                          format(draftFilters.dateRange.from, "LLL dd, y")
                        )
                      ) : (
                        <span>Pick a date range</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      initialFocus
                      mode="range"
                      defaultMonth={draftFilters.dateRange?.from}
                      selected={draftFilters.dateRange}
                      onSelect={(range) => setDraftFilters(prev => ({ ...prev, dateRange: range }))}
                      numberOfMonths={2}
                    />
                  </PopoverContent>
                </Popover>
              </div>

              {/* Status Filter */}
              <div className="space-y-2 lg:col-span-1 md:col-span-2">
                <Label>Status</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 items-center pt-1">
                  {allStatusesForFilter.map(status => ( // Use allStatusesForFilter
                    <div key={status} className="flex items-center space-x-2">
                      <Checkbox 
                        id={`status-${status}`}
                        checked={draftFilters.statuses?.includes(status)}
                        onCheckedChange={(checked) => {
                          setDraftFilters(prev => ({
                            ...prev,
                            statuses: checked 
                              ? [...(prev.statuses || []), status] 
                              : (prev.statuses || []).filter(s => s !== status)
                          }));
                        }}
                      />
                      <Label htmlFor={`status-${status}`} className="font-normal capitalize text-sm">
                        {status.replace("_", " ")}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <Button variant="ghost" onClick={handleClearFilters}>
                <XIcon className="mr-2 h-4 w-4" /> Clear Filters
              </Button>
              <Button onClick={handleApplyFilters} disabled={isFetching}>
                <FilterIcon className="mr-2 h-4 w-4" /> Apply Filters
              </Button>
            </div>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>A list of recent bid activities. {isFetching && "(Updating...)"}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Profile Name</TableHead>
              <TableHead>Vacancy ID</TableHead>
              <TableHead>Submitted At</TableHead>
              <TableHead>Response At</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [...Array(ITEMS_PER_PAGE)].map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  <TableCell><Skeleton className="h-5 w-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="h-5 w-12" /></TableCell>
                </TableRow>
              ))
            ) : isError ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-red-600">
                  <AlertTriangle className="mx-auto h-6 w-6 mb-2" />
                  Error loading bid history: {error?.message || "An unexpected error occurred."}
                </TableCell>
              </TableRow>
            ) : currentTableData.length > 0 ? (
              currentTableData.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-medium">{log.profileName}</TableCell>
                  <TableCell>{log.vacancyId}</TableCell>
                  <TableCell>{format(new Date(log.submittedAt), 'PPpp')}</TableCell>
                  <TableCell>{log.responseAt ? format(new Date(log.responseAt), 'PPpp') : 'N/A'}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(log.status)} className="capitalize">
                      {log.status.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{log.score ?? 'N/A'}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  No bid logs found matching your criteria.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {totalPages > 0 && ( // Show pagination only if there are pages
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious 
                href="#" 
                onClick={(e) => { e.preventDefault(); if(currentPage > 1) setCurrentPage(prev => prev - 1); }}
                className={currentPage === 1 ? "pointer-events-none opacity-50" : undefined} 
              />
            </PaginationItem>
            {/* Simplified pagination display for brevity, can be enhanced */}
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(pageNum => (
              (totalPages <= 5 || (pageNum >= currentPage - 1 && pageNum <= currentPage + 1) || pageNum === 1 || pageNum === totalPages) ? (
                <PaginationItem key={pageNum}>
                  <PaginationLink 
                    href="#" 
                    onClick={(e) => { e.preventDefault(); setCurrentPage(pageNum); }}
                    isActive={currentPage === pageNum}
                  >
                    {pageNum}
                  </PaginationLink>
                </PaginationItem>
              ) : ( (currentPage > 3 && pageNum === currentPage - 2) || (currentPage < totalPages - 2 && pageNum === currentPage + 2) ) ? (
                <PaginationEllipsis key={`ellipsis-${pageNum}`} />
              ) : null
            ))}
            <PaginationItem>
              <PaginationNext 
                href="#" 
                onClick={(e) => { e.preventDefault(); if(currentPage < totalPages) setCurrentPage(prev => prev + 1); }}
                className={currentPage === totalPages ? "pointer-events-none opacity-50" : undefined}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
