import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '../DashboardPage';
import { AuthContext, AuthContextType } from '@/contexts/AuthContext';
import * as dashboardQueries from '@/hooks/useDashboardQueries';
import i18n from '@/i18n'; // Your i18n configuration

const queryClient = new QueryClient();

// Mocks
jest.mock('@/hooks/useDashboardQueries');

const mockUseDashboardSummaryStats = dashboardQueries.useDashboardSummaryStats as jest.Mock;
const mockUseIndividualDashboardStats = dashboardQueries.useIndividualDashboardStats as jest.Mock;
const mockUseAgencyDashboardStats = dashboardQueries.useAgencyDashboardStats as jest.Mock;

const renderDashboardPage = (authContextValue: Partial<AuthContextType>) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authContextValue as AuthContextType}>
        <I18nextProvider i18n={i18n}>
          <DashboardPage />
        </I18nextProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('DashboardPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    mockUseDashboardSummaryStats.mockReturnValue({ data: null, isLoading: true, isError: false });
    mockUseIndividualDashboardStats.mockReturnValue({ data: null, isLoading: true, isError: false });
    mockUseAgencyDashboardStats.mockReturnValue({ data: null, isLoading: true, isError: false });
  });

  describe('Loading States', () => {
    it('renders skeletons when loading for individual user', () => {
      renderDashboardPage({ user: { account_type: 'individual' } });
      // Expect 4 skeletons for individual view (Active Profiles, Running Autobid, Recent Bids, My Profile Performance)
      const skeletons = screen.getAllByRole('heading', { name: /loading/i }); // A bit generic, better to target specific skeleton structure if possible
      // This is a basic check, ideally we'd check for specific skeleton components or structure
      // For now, let's assume MetricCardSkeleton renders a heading with "Loading..." or similar accessible name during skeleton state
      // This count might need adjustment based on how MetricCardSkeleton is actually implemented and how many are expected
      // For now, we know that there are 4 cards for individual, 5 for agency.
      // The skeleton component itself has a heading, so we expect that many "loading" headings.
      // This is a placeholder, a more robust way would be to check for the specific skeleton component.
      // For now, we will check for the number of MetricCardSkeleton components.
      // The MetricCardSkeleton uses <Skeleton className="h-5 w-2/3" /> for title, so we can't query by text.
      // Let's check the number of cards by the number of "Card" roles.
      const cards = screen.getAllByRole("generic").filter(el => el.classList.contains('rounded-lg') && el.classList.contains('border'));
      expect(cards.length).toBe(4); 
    });

    it('renders skeletons when loading for agency user', () => {
      renderDashboardPage({ user: { account_type: 'agency' } });
      // Expect 5 skeletons for agency view
      const cards = screen.getAllByRole("generic").filter(el => el.classList.contains('rounded-lg') && el.classList.contains('border'));
      expect(cards.length).toBe(5);
    });
  });

  describe('Error States', () => {
    it('renders error message when summary stats fail', () => {
      mockUseDashboardSummaryStats.mockReturnValue({ data: null, isLoading: false, isError: true, error: { message: 'Summary Error' } });
      renderDashboardPage({ user: { account_type: 'individual' } });
      expect(screen.getByText(/Error Loading Dashboard Data/i)).toBeInTheDocument();
      expect(screen.getByText(/Summary Error/i)).toBeInTheDocument();
    });

    it('renders error message when individual stats fail for individual user', () => {
      mockUseDashboardSummaryStats.mockReturnValue({ data: {}, isLoading: false, isError: false });
      mockUseIndividualDashboardStats.mockReturnValue({ data: null, isLoading: false, isError: true, error: { message: 'Individual Error' } });
      renderDashboardPage({ user: { account_type: 'individual' } });
      expect(screen.getByText(/Error Loading Dashboard Data/i)).toBeInTheDocument();
      expect(screen.getByText(/Individual Error/i)).toBeInTheDocument();
    });

    it('renders error message when agency stats fail for agency user', () => {
      mockUseDashboardSummaryStats.mockReturnValue({ data: {}, isLoading: false, isError: false });
      mockUseAgencyDashboardStats.mockReturnValue({ data: null, isLoading: false, isError: true, error: { message: 'Agency Error' } });
      renderDashboardPage({ user: { account_type: 'agency' } });
      expect(screen.getByText(/Error Loading Dashboard Data/i)).toBeInTheDocument();
      expect(screen.getByText(/Agency Error/i)).toBeInTheDocument();
    });
  });

  describe('Individual User View', () => {
    beforeEach(() => {
      mockUseDashboardSummaryStats.mockReturnValue({
        data: { activeProfilesCount: 3, runningAutobidJobsCount: 2, recentBidsCount: 10, runningAutobidJobsStatus: 'active' },
        isLoading: false, isError: false,
      });
      mockUseIndividualDashboardStats.mockReturnValue({
        data: { averageBidSuccessRate: '75%' },
        isLoading: false, isError: false,
      });
      mockUseAgencyDashboardStats.mockReturnValue({ data: null, isLoading: false, isError: false }); // Not used by individual
    });

    it('renders correct cards for individual user', () => {
      renderDashboardPage({ user: { account_type: 'individual' } });

      expect(screen.getByText(/Active Profiles/i)).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // Active Profiles Count

      expect(screen.getByText(/Running Autobid Jobs/i)).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Running Autobid Jobs Count
      
      expect(screen.getByText(/Recent Bids/i)).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument(); // Recent Bids Count

      expect(screen.getByText(/My Profile Performance/i)).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument(); // Average Bid Success Rate
      
      expect(screen.queryByText(/Managed Client Profiles/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Team Activity Overview/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Agency Performance Metrics/i)).not.toBeInTheDocument();
    });
  });

  describe('Agency User View', () => {
    beforeEach(() => {
      mockUseDashboardSummaryStats.mockReturnValue({
        data: { runningAutobidJobsCount: 5, recentBidsCount: 25, runningAutobidJobsStatus: 'active', activeProfilesCount: 10 }, // activeProfilesCount is also used as a fallback for managed by agency
        isLoading: false, isError: false,
      });
      mockUseIndividualDashboardStats.mockReturnValue({ data: null, isLoading: false, isError: false }); // Not used by agency
      mockUseAgencyDashboardStats.mockReturnValue({
        data: { managedClientProfilesCount: 8, teamMembersCount: 4, recentTeamBidsCount: 100, clientSatisfactionScore: '4.2/5 Stars' },
        isLoading: false, isError: false,
      });
    });

    it('renders correct cards for agency user', () => {
      renderDashboardPage({ user: { account_type: 'agency' } });

      expect(screen.getByText(/Managed Client Profiles/i)).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument(); // Managed Client Profiles Count

      expect(screen.getByText(/Running Autobid Jobs/i)).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument(); // Running Autobid Jobs Count
      
      expect(screen.getByText(/Recent Bids/i)).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument(); // Recent Bids Count

      expect(screen.getByText(/Team Activity Overview/i)).toBeInTheDocument();
      expect(screen.getByText(/4 Team Members/i)).toBeInTheDocument(); 
      expect(screen.getByText(/100 recent team bids/i)).toBeInTheDocument(); 

      expect(screen.getByText(/Agency Performance Metrics/i)).toBeInTheDocument();
      expect(screen.getByText('4.2/5 Stars')).toBeInTheDocument(); // Client Satisfaction Score
      
      expect(screen.queryByText(/^Active Profiles$/i)).not.toBeInTheDocument(); // Should be "Managed Client Profiles"
      expect(screen.queryByText(/My Profile Performance/i)).not.toBeInTheDocument();
    });
  });
});
