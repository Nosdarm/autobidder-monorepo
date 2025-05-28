import React from 'react'; // Removed useEffect, useState
import { useParams, Link } from 'react-router-dom';
import { format } from 'date-fns'; // Removed subDays, addDays as they are for mock data gen
import { ArrowLeftIcon, AlertTriangle } from 'lucide-react'; // Added AlertTriangle

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'; // Removed CardFooter
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton'; // For loading state
import { useBidLogEntry } from '@/hooks/useBidHistoryQueries'; // Import the hook
import type { BidStatus, BidLogEntry } from '@/services/bidHistoryService'; // Import types


// This function is now primarily for styling, data comes from hook
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

export default function BidDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: bidLog, isLoading, isError, error } = useBidLogEntry(id);

  if (isLoading) {
    return (
      <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-1/3" /> {/* Title Skeleton */}
          <Skeleton className="h-10 w-44" /> {/* Back Button Skeleton */}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-1/2 mb-2" /> {/* Card Title Skeleton */}
            <Skeleton className="h-4 w-3/4" /> {/* Card Description Skeleton */}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              {[...Array(6)].map((_, i) => (
                <div key={i}>
                  <Skeleton className="h-4 w-1/3 mb-1" /> {/* Label Skeleton */}
                  <Skeleton className="h-5 w-2/3" /> {/* Value Skeleton */}
                </div>
              ))}
            </div>
            <div className="pt-4">
              <Skeleton className="h-6 w-1/4 mb-2" /> {/* API Response Title Skeleton */}
              <Skeleton className="h-40 w-full" /> {/* API Response Content Skeleton */}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError || !bidLog) {
    return (
      <div className="p-4 md:p-6 text-center max-w-4xl mx-auto">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
        <h1 className="mt-4 text-2xl font-semibold text-red-600">
          {isError ? "Error Loading Bid Details" : "Bid Not Found"}
        </h1>
        <p className="mt-2 text-muted-foreground mb-6">
          {isError ? error?.message : `The bid log entry with ID "${id}" could not be found.`}
        </p>
        <Button asChild variant="outline">
          <Link to="/bids">
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Bid History
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Bid Details</h1>
        <Button asChild variant="outline">
          <Link to="/bids">
            <ArrowLeftIcon className="mr-2 h-4 w-4" />
            Back to Bid History
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Log ID: {bidLog.id}</CardTitle>
          <CardDescription>
            Details for bid placed on Vacancy ID: {bidLog.vacancyId}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Profile Name</h4>
              <p>{bidLog.profileName}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Vacancy ID</h4>
              <p>{bidLog.vacancyId}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Submitted At</h4>
              <p>{format(new Date(bidLog.submittedAt), 'PPpp')}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Response At</h4>
              <p>{bidLog.responseAt ? format(new Date(bidLog.responseAt), 'PPpp') : 'N/A'}</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Status</h4>
              <Badge variant={getStatusBadgeVariant(bidLog.status)} className="capitalize">
                {bidLog.status.replace("_", " ")}
              </Badge>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-muted-foreground">Match Score</h4>
              <p>{bidLog.score ?? 'N/A'}</p>
            </div>
          </div>

          {bidLog.apiResponse && (
            <div className="pt-4">
              <h4 className="text-lg font-semibold mb-2">API Response Payload</h4>
              <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto whitespace-pre-wrap break-all"> {/* Use theme-aware bg-muted */}
                <code>{JSON.stringify(bidLog.apiResponse, null, 2)}</code>
              </pre>
            </div>
          )}
        </CardContent>
        {/* <CardFooter>
          Optional footer content
        </CardFooter> */}
      </Card>
    </div>
  );
}
