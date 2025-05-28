import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next'; // Import useTranslation
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, Briefcase, List, ExternalLink, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useDashboardSummaryStats } from '@/hooks/useDashboardQueries';
import type { AutobidJobStatus } from '@/services/dashboardService';

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
  const { data: summaryStats, isLoading, isError, error } = useDashboardSummaryStats();

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4 md:p-6">
        <MetricCardSkeleton />
        <MetricCardSkeleton />
        <MetricCardSkeleton />
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
  
  const activeProfilesCount = summaryStats?.activeProfilesCount ?? 0;
  const runningAutobidJobsCount = summaryStats?.runningAutobidJobsCount ?? 0;
  const runningAutobidJobsStatus = summaryStats?.runningAutobidJobsStatus;
  const recentBidsCount = summaryStats?.recentBidsCount ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4 md:p-6">
      {/* Active Profiles Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{t('dashboard.activeProfiles.title')}</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{activeProfilesCount}</div>
          <p className="text-xs text-muted-foreground">
            {t('dashboard.activeProfiles.description')}
          </p>
        </CardContent>
        <CardFooter>
          <Button asChild size="sm">
            <Link to="/profiles">{t('dashboard.activeProfiles.button')}</Link>
          </Button>
        </CardFooter>
      </Card>

      {/* Running Autobid Jobs Card */}
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
