import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next'; // Import useTranslation
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, Briefcase, List, ExternalLink, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/components/contexts/AuthContext'; // Import useAuth
import {
  useDashboardSummaryStats,
  useIndividualDashboardStats,
  useAgencyDashboardStats,
} from '@/hooks/useDashboardQueries';
import type { AutobidJobStatus } from '@/services/dashboardService';
import { BarChart, Users2, ShieldCheck, TrendingUp, Building, Activity, Star } from 'lucide-react'; // Added more icons

// Helper component for Metric Card Skeleton
const MetricCardSkeleton = () => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <Skeleton className="h-5 w-2/3" /> {/* Title */}
      <Skeleton className="h-5 w-5" /> {/* Icon */}
    </CardHeader>
    <CardContent>
      <Skeleton className="h-8 w-1/2 mb-1" /> {/* Value */}
      <Skeleton className="h-3 w-full" /> {/* Description */}
    </CardContent>
    <CardFooter>
      <Skeleton className="h-8 w-2/3" /> {/* Button/Link Skeleton */}
    </CardFooter>
  </Card>
);

export default function DashboardPage() {
  const { t } = useTranslation(); // Initialize useTranslation
  const { user } = useAuth(); // Get user from AuthContext
  const accountType = user?.account_type || 'individual'; // Default to individual if undefined

  const { data: summaryStats, isLoading: isLoadingSummary, isError: isErrorSummary, error: errorSummary } = useDashboardSummaryStats();
  const { data: individualStats, isLoading: isLoadingIndividual, isError: isErrorIndividual, error: errorIndividual } = useIndividualDashboardStats({
    enabled: accountType === 'individual', // Only fetch if account type is individual
  });
  const { data: agencyStats, isLoading: isLoadingAgency, isError: isErrorAgency, error: errorAgency } = useAgencyDashboardStats({
    enabled: accountType === 'agency', // Only fetch if account type is agency
  });

  const isLoading = isLoadingSummary || (accountType === 'individual' && isLoadingIndividual) || (accountType === 'agency' && isLoadingAgency);
  // Combine error states - show a general error if any of the relevant queries fail
  const isError = isErrorSummary || (accountType === 'individual' && isErrorIndividual) || (accountType === 'agency' && isErrorAgency);
  const error = errorSummary || errorIndividual || errorAgency;


  const getAutobidJobStatusBadge = (status?: AutobidJobStatus) => {
    if (!status) return <Badge className="capitalize">{t('dashboard.autobidStatus.unknown')}</Badge>;
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500 hover:bg-green-600 capitalize">{t('dashboard.autobidStatus.active')}</Badge>;
      case 'inactive':
        return <Badge variant="outline" className="capitalize">{t('dashboard.autobidStatus.inactive')}</Badge>;
      case 'error':
        return <Badge variant="destructive" className="capitalize">{t('dashboard.autobidStatus.error')}</Badge>;
      default:
        return <Badge className="capitalize">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4 md:p-6">
        {[...Array(accountType === 'agency' ? 5 : 4)].map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 md:p-6 text-center">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
        <h2 className="mt-4 text-xl font-semibold text-red-600">{t('dashboard.error.title')}</h2>
        <p className="mt-2 text-muted-foreground">
          {error?.message || t('dashboard.error.defaultMessage')}
        </p>
      </div>
    );
  }
  
  // Common Stats
  const runningAutobidJobsCount = summaryStats?.runningAutobidJobsCount ?? 0;
  const runningAutobidJobsStatus = summaryStats?.runningAutobidJobsStatus;
  const recentBidsCount = summaryStats?.recentBidsCount ?? 0;

  // Individual Specific Stats
  const activeProfilesCount = summaryStats?.activeProfilesCount ?? 0; // Used by Individual
  const averageBidSuccessRate = individualStats?.averageBidSuccessRate ?? t('dashboard.individualPerformance.loading');

  // Agency Specific Stats
  const managedClientProfilesCount = agencyStats?.managedClientProfilesCount ?? activeProfilesCount; // Fallback for agency if specific not loaded
  const teamMembersCount = agencyStats?.teamMembersCount ?? 0;
  const recentTeamBidsCount = agencyStats?.recentTeamBidsCount ?? 0;
  const clientSatisfactionScore = agencyStats?.clientSatisfactionScore ?? t('dashboard.agencyPerformance.loading');


  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4 md:p-6">
      {/* Common Card: Running Autobid Jobs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{t('dashboard.runningAutobidJobs.title')}</CardTitle>
          <Briefcase className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{runningAutobidJobsCount}</div>
          <div className="flex items-center text-xs">
            {getAutobidJobStatusBadge(runningAutobidJobsStatus)}
            <span className="text-muted-foreground ml-1">{t('dashboard.runningAutobidJobs.descriptionSuffix')}</span>
          </div>
        </CardContent>
        {/* Optional Footer for actions if needed later */}
      </Card>

      {/* Recent Bids Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{t('dashboard.recentBids.title')}</CardTitle>
          <List className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{recentBidsCount}</div>
          <p className="text-xs text-muted-foreground">
            {t('dashboard.recentBids.description')}
          </p>
        </CardContent>
        <CardFooter>
          <Button asChild variant="outline" size="sm">
            <Link to="/bids">
              {t('dashboard.recentBids.button')}
              <ExternalLink className="ml-2 h-3 w-3" />
            </Link>
          </Button>
        </CardFooter>
      </Card>

      {/* Placeholder for future cards if needed */}
    </div>
  );
}
