// queryKeys.ts

export const profileKeys = {
  all: ['profiles'] as const,
  lists: () => [...profileKeys.all, 'list'] as const,
  list: (filters: string) => [...profileKeys.lists(), { filters }] as const, // Example if filtering lists
  details: () => [...profileKeys.all, 'detail'] as const,
  detail: (id: string) => [...profileKeys.details(), id] as const,
};

export const aiPromptKeys = {
  all: ['aiPrompts'] as const,
  lists: () => [...aiPromptKeys.all, 'list'] as const,
  list: (filters: string) => [...aiPromptKeys.lists(), { filters }] as const, // Example if filtering lists
  details: () => [...aiPromptKeys.all, 'detail'] as const,
  detail: (id: string) => [...aiPromptKeys.details(), id] as const,
};

export const autobidSettingsKeys = {
  all: ['autobidSettings'] as const,
  settingsForAllProfiles: () => [...autobidSettingsKeys.all, 'allProfiles'] as const,
  settingsForProfile: (profileId: string) => [...autobidSettingsKeys.all, 'detail', profileId] as const,
};

export const bidHistoryKeys = {
  all: ['bidHistory'] as const,
  lists: () => [...bidHistoryKeys.all, 'list'] as const,
  list: (filters: object, page: number, limit: number) => 
    [...bidHistoryKeys.lists(), { ...filters, page, limit }] as const,
  details: () => [...bidHistoryKeys.all, 'detail'] as const,
  detail: (id: string) => [...bidHistoryKeys.details(), id] as const,
};

export const mlAnalyticsKeys = {
  all: ['mlAnalytics'] as const,
  data: (dateRange?: object) => [...mlAnalyticsKeys.all, 'data', dateRange || {}] as const,
  metrics: (dateRange?: object) => [...mlAnalyticsKeys.data(dateRange), 'metrics'] as const,
  charts: (dateRange?: object) => [...mlAnalyticsKeys.data(dateRange), 'charts'] as const,
  lineChart: (dateRange?: object) => [...mlAnalyticsKeys.charts(dateRange), 'line'] as const,
  barChart: (dateRange?: object) => [...mlAnalyticsKeys.charts(dateRange), 'bar'] as const,
  jobsWithScores: (dateRange?: object) => [...mlAnalyticsKeys.data(dateRange), 'jobsWithScores'] as const, // Added
};

export const dashboardKeys = {
  all: ['dashboard'] as const,
  summaryStats: () => [...dashboardKeys.all, 'summaryStats'] as const,
  individualStats: () => [...dashboardKeys.all, 'individualStats'] as const,
  agencyStats: () => [...dashboardKeys.all, 'agencyStats'] as const,
};
