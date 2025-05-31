import React, { useState } from 'react';
import { format, subDays } from 'date-fns';
import type { DateRange } from 'react-day-picker';
import { CalendarIcon, Target, Repeat, Sigma, CheckCircle, LineChart as LineChartIcon, BarChart2 as BarChartIcon, AlertTriangle } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  // PieChart, Pie, Cell,
} from 'recharts';

import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Skeleton } from '@/components/ui/skeleton'; // For loading states
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"; // Import table components
import { 
  useMLMetricsCards, 
  useMLLineChartData, 
  useMLBarChartData,
  useMLJobsWithScores // Added hook
} from '@/hooks/useMLAnalyticsQueries';
import type { Job as JobData } from '@/services/mlAnalyticsService'; // Added JobData import
// MetricCardData and ChartDataPoint types are now imported from the service or defined in hooks if needed for props


// Map titles to icons (since icon component cannot be in JSON from API)
const iconMap: Record<string, React.ElementType> = {
  "Precision@k": Target,
  "Recall@k": Repeat,
  "F1 Score": Sigma,
  "Overall Accuracy": CheckCircle,
};


export default function MLAnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29), // Default to last 30 days
    to: new Date(),
  });

  const { 
    data: metricsCardsData = [], 
    isLoading: isLoadingMetrics, 
    isError: isErrorMetrics, 
    error: errorMetrics 
  } = useMLMetricsCards(dateRange);

  const { 
    data: lineChartData = [], 
    isLoading: isLoadingLineChart, 
    isError: isErrorLineChart, 
    error: errorLineChart 
  } = useMLLineChartData(dateRange);

  const { 
    data: barChartData = [], 
    isLoading: isLoadingBarChart, 
    isError: isErrorBarChart, 
    error: errorBarChart 
  } = useMLBarChartData(dateRange);

  const {
    data: jobsWithScoresData = [],
    isLoading: isLoadingJobsWithScores,
    isError: isErrorJobsWithScores,
    error: errorJobsWithScores,
  } = useMLJobsWithScores(dateRange);


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
    </Card>
  );

  // Helper component for Chart Skeleton
  const ChartSkeleton = ({ title }: { title: string }) => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Skeleton className="mr-2 h-5 w-5" /> {/* Icon */}
          {title}
        </CardTitle>
        <Skeleton className="h-4 w-3/4" /> {/* Description */}
      </CardHeader>
      <CardContent className="h-[350px] pt-4 flex items-center justify-center">
        <Skeleton className="h-full w-full" />
      </CardContent>
    </Card>
  );

  const JobsTableSkeleton = () => (
    <Card>
      <CardHeader>
        <CardTitle>
          <Skeleton className="h-6 w-1/2" />
        </CardTitle>
        <CardDescription>
          <Skeleton className="h-4 w-3/4" />
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex justify-between space-x-4 p-2 border-b">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-5 w-1/4" />
              <Skeleton className="h-5 w-1/4" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
  
  // Helper component for Error Display
  const ErrorDisplay = ({ title, error }: { title: string, error: Error | null }) => (
     <Card>
      <CardHeader>
        <CardTitle className="flex items-center text-red-600">
          <AlertTriangle className="mr-2 h-5 w-5" />
          Error: {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-red-500">{error?.message || "An unexpected error occurred."}</p>
      </CardContent>
    </Card>
  );


  return (
    <div className="p-4 md:p-6 space-y-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">ML Model Analytics</h1>
          <p className="text-muted-foreground">
            Insights into model performance and operational metrics.
          </p>
        </div>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              id="date-range-picker"
              variant={"outline"}
              className="w-full sm:w-auto justify-start text-left font-normal min-w-[240px]"
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange?.from ? (
                dateRange.to ? (
                  <>
                    {format(dateRange.from, "LLL dd, y")} - {format(dateRange.to, "LLL dd, y")}
                  </>
                ) : (
                  format(dateRange.from, "LLL dd, y")
                )
              ) : (
                <span>Pick a date range</span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="end">
            <Calendar
              initialFocus
              mode="range"
              defaultMonth={dateRange?.from}
              selected={dateRange}
              onSelect={setDateRange}
              numberOfMonths={2}
            />
          </PopoverContent>
        </Popover>
      </div>

      {/* Key Metrics Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {isLoadingMetrics ? (
            Array.from({ length: 4 }).map((_, index) => <MetricCardSkeleton key={`metric-skeleton-${index}`} />)
          ) : isErrorMetrics ? (
            <div className="col-span-full">
              <ErrorDisplay title="Loading Key Metrics" error={errorMetrics} />
            </div>
          ) : (
            metricsCardsData.map((metric) => {
              const IconComponent = iconMap[metric.title] || Target; // Default icon
              return (
                <Card key={metric.title}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
                    <IconComponent className="h-5 w-5 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{metric.value}</div>
                    {/* Description can be added to MetricCardData if needed from API */}
                    {/* <p className="text-xs text-muted-foreground pt-1">{metric.description}</p> */}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </section>

      {/* Performance Charts Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Performance Charts</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Line Chart: Performance Over Time */}
          {isLoadingLineChart ? (
            <ChartSkeleton title="Performance Over Time" />
          ) : isErrorLineChart ? (
            <ErrorDisplay title="Performance Over Time Chart" error={errorLineChart} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <LineChartIcon className="mr-2 h-5 w-5 text-primary" />
                  Performance Over Time
                </CardTitle>
                <CardDescription>F1 Score trend for the selected period.</CardDescription>
              </CardHeader>
              <CardContent className="h-[350px] pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={[0.6, 1.0]} tickFormatter={(value) => value.toFixed(2)} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                      labelStyle={{ color: "hsl(var(--card-foreground))" }}
                    />
                    <Legend wrapperStyle={{fontSize: "14px"}} />
                    <Line type="monotone" dataKey="value" name="F1 Score" stroke="hsl(var(--primary))" strokeWidth={2} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Bar Chart: Feature Importance */}
          {isLoadingBarChart ? (
            <ChartSkeleton title="Feature Importance" />
          ) : isErrorBarChart ? (
            <ErrorDisplay title="Feature Importance Chart" error={errorBarChart} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChartIcon className="mr-2 h-5 w-5 text-primary" />
                  Feature Importance
                </CardTitle>
                <CardDescription>Relative importance of features in the model.</CardDescription>
              </CardHeader>
              <CardContent className="h-[350px] pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis dataKey="name" type="category" stroke="hsl(var(--muted-foreground))" fontSize={12} width={120} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                      labelStyle={{ color: "hsl(var(--card-foreground))" }}
                      formatter={(value: number) => `${value}%`}
                    />
                    <Legend wrapperStyle={{fontSize: "14px"}} />
                    <Bar dataKey="value" name="Importance" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Jobs with Predicted Scores Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Jobs Overview with Predicted Scores</h2>
        {isLoadingJobsWithScores ? (
          <JobsTableSkeleton />
        ) : isErrorJobsWithScores ? (
          <ErrorDisplay title="Loading Jobs Data" error={errorJobsWithScores} />
        ) : jobsWithScoresData.length === 0 ? (
           <Card>
            <CardHeader>
              <CardTitle>Jobs Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <p>No jobs data available for the selected date range.</p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Jobs & Scores</CardTitle>
              <CardDescription>
                List of recent jobs and their predicted success scores.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Upwork ID</TableHead>
                    <TableHead className="text-right">Predicted Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobsWithScoresData.map((job: JobData) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium">{job.title}</TableCell>
                      <TableCell>{job.upwork_job_id || 'N/A'}</TableCell>
                      <TableCell className="text-right">
                        {job.predicted_score != null ? job.predicted_score.toFixed(1) : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
}
