import React, { useState, useEffect } from 'react';
import { format, subDays, addDays } from 'date-fns';
import { CalendarIcon, DownloadIcon, FilterIcon, XIcon, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { useTranslation } from 'react-i18next'; // Import useTranslation

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { DateRange } from 'react-day-picker';
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from '@/components/ui/badge';
import { useBidHistory } from '@/hooks/useBidHistoryQueries';
import type { BidLogEntry, BidStatus, FilterState } from '@/services/bidHistoryService';

// Mock Profile Data for Select - This can be fetched via React Query if needed in a real app
const mockProfilesForFilter = [
  { id: 'profile1', name: 'My Main Upwork Profile' },
  { id: 'profile2', name: 'Agency Client - Tech Lead Roles' },
  { id: 'profile3', name: 'Side Gig - Quick Projects' },
];

// These status values should ideally come from a shared source or be translated if they appear in UI directly
const allStatusesForFilter: BidStatus[] = ["submitted", "successful", "failed", "viewed", "pending_review"];

const ITEMS_PER_PAGE = 10;

export default function BidHistoryPage() {
  const { t } = useTranslation(); // Initialize useTranslation
  const { showToastSuccess } = useToast();
  
  const initialFilters: FilterState = {
    profileId: null,
    dateRange: undefined,
    statuses: [],
  };
  const [activeFilters, setActiveFilters] = useState<FilterState>(initialFilters);
  const [draftFilters, setDraftFilters] = useState<FilterState>(initialFilters);
  const [currentPage, setCurrentPage] = useState(1);

  const { 
    data: paginatedData, 
    isLoading, 
    isError, 
    error,
    isFetching,
  } = useBidHistory(activeFilters, currentPage, ITEMS_PER_PAGE);

  const currentTableData = paginatedData?.logs || [];
  const totalPages = paginatedData?.totalPages || 0;

  const handleApplyFilters = () => {
    setActiveFilters(draftFilters);
    setCurrentPage(1); 
  };

  const handleClearFilters = () => {
    setDraftFilters(initialFilters);
    setActiveFilters(initialFilters);
    setCurrentPage(1);
  };

  const handleExportCSV = () => {
    // For export, you might want to fetch all data matching current filters
    showToastSuccess(t('bidHistory.exportNotImplemented')); 
    console.log("Export CSV clicked. Current active filters:", activeFilters);
    console.log("Currently displayed data:", currentTableData);
  };
  
  const getStatusBadgeVariant = (status: BidStatus): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "successful": return "default";
      case "submitted": return "secondary";
      case "pending_review": return "outline";
      case "viewed": return "outline";
      case "failed": return "destructive";
      default: return "secondary";
    }
  };
  
  // Helper for status translation
  const translateStatus = (status: BidStatus) => {
    return t(`bidHistory.statusLabels.${status.replace("_", "")}` as const, status.replace("_", " "));
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{t('bidHistory.title')}</h1>
          <p className="text-muted-foreground">
            {t('bidHistory.description')}
          </p>
        </div>
        <Button onClick={handleExportCSV} variant="outline">
          <DownloadIcon className="mr-2 h-4 w-4" /> {t('bidHistory.exportButton')}
        </Button>
      </div>

      <Collapsible className="space-y-4">
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="w-full sm:w-auto">
            <FilterIcon className="mr-2 h-4 w-4" /> {t('bidHistory.filters.showFiltersButton')}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <Card className="p-6 shadow-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Label htmlFor="profile-filter">{t('bidHistory.filters.profileLabel')}</Label>
                <Select 
                  value={draftFilters.profileId || ""}
                  onValueChange={(value) => setDraftFilters(prev => ({ ...prev, profileId: value === "all" ? null : value }))}
                >
                  <SelectTrigger id="profile-filter">
                    <SelectValue placeholder={t('bidHistory.filters.allProfilesPlaceholder')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t('bidHistory.filters.allProfilesOption')}</SelectItem>
                    {mockProfilesForFilter.map(profile => (
                      <SelectItem key={profile.id} value={profile.id}>{profile.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="date-range-filter">{t('bidHistory.filters.dateRangeLabel')}</Label>
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
                        <span>{t('bidHistory.filters.dateRangePlaceholder')}</span>
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

              <div className="space-y-2 lg:col-span-1 md:col-span-2">
                <Label>{t('bidHistory.filters.statusLabel')}</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 items-center pt-1">
                  {allStatusesForFilter.map(status => (
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
                        {translateStatus(status)}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <Button variant="ghost" onClick={handleClearFilters}>
                <XIcon className="mr-2 h-4 w-4" /> {t('bidHistory.filters.clearFiltersButton')}
              </Button>
              <Button onClick={handleApplyFilters} disabled={isFetching}>
                <FilterIcon className="mr-2 h-4 w-4" /> {t('bidHistory.filters.applyFiltersButton')}
              </Button>
            </div>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>{t('bidHistory.table.caption')} {isFetching && `(${t('bidHistory.table.updatingCaptionSuffix')})`}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>{t('bidHistory.table.headerProfileName')}</TableHead>
              <TableHead>{t('bidHistory.table.headerVacancyId')}</TableHead>
              <TableHead>{t('bidHistory.table.headerSubmittedAt')}</TableHead>
              <TableHead>{t('bidHistory.table.headerResponseAt')}</TableHead>
              <TableHead>{t('bidHistory.table.headerStatus')}</TableHead>
              <TableHead className="text-right">{t('bidHistory.table.headerScore')}</TableHead>
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
                  {t('bidHistory.table.errorLoading', { message: error?.message || t('bidHistory.table.defaultError') })}
                </TableCell>
              </TableRow>
            ) : currentTableData.length > 0 ? (
              currentTableData.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-medium">{log.profileName}</TableCell>
                  <TableCell>{log.vacancyId}</TableCell>
                  <TableCell>{format(new Date(log.submittedAt), 'PPpp')}</TableCell>
                  <TableCell>{log.responseAt ? format(new Date(log.responseAt), 'PPpp') : t('bidHistory.table.notApplicable')}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(log.status)} className="capitalize">
                      {translateStatus(log.status)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{log.score ?? t('bidHistory.table.notApplicableScore')}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  {t('bidHistory.table.noLogsFound')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {totalPages > 0 && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious 
                href="#" 
                onClick={(e) => { e.preventDefault(); if(currentPage > 1) setCurrentPage(prev => prev - 1); }}
                className={currentPage === 1 ? "pointer-events-none opacity-50" : undefined} 
                aria-label={t('bidHistory.pagination.previous')}
              />
            </PaginationItem>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(pageNum => (
              (totalPages <= 5 || (pageNum >= currentPage - 1 && pageNum <= currentPage + 1) || pageNum === 1 || pageNum === totalPages) ? (
                <PaginationItem key={pageNum}>
                  <PaginationLink 
                    href="#" 
                    onClick={(e) => { e.preventDefault(); setCurrentPage(pageNum); }}
                    isActive={currentPage === pageNum}
                    aria-label={t('bidHistory.pagination.page', { pageNum })}
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
                aria-label={t('bidHistory.pagination.next')}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
