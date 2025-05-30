import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProfilesPage from '../ProfilesPage';
import { AuthContext, AuthContextType } from '@/contexts/AuthContext';
import * as profileQueries from '@/hooks/useProfileQueries';
import i18n from '@/i18n'; // Your i18n configuration
import ProfileCreateForm from '@/components/profiles/ProfileCreateForm';

const queryClient = new QueryClient();

// Mocks
jest.mock('@/hooks/useProfileQueries');
jest.mock('@/components/profiles/ProfileCreateForm', () => jest.fn(() => <div data-testid="profile-create-form">Mocked ProfileCreateForm</div>));


const mockUseProfiles = profileQueries.useProfiles as jest.Mock;
const mockUseCreateProfile = profileQueries.useCreateProfile as jest.Mock;
const mockUseUpdateProfile = profileQueries.useUpdateProfile as jest.Mock;
const mockUseDeleteProfile = profileQueries.useDeleteProfile as jest.Mock;

const mockProfilesData = [
  { id: '1', name: 'Test Profile 1', profile_type: 'personal', autobid_enabled: true, createdAt: new Date().toISOString(), skills: ['React'], experience_level: 'intermediate' },
  { id: '2', name: 'Test Profile 2', profile_type: 'agency', autobid_enabled: false, createdAt: new Date().toISOString(), skills: [], experience_level: undefined },
];

const renderProfilesPage = (authContextValue: Partial<AuthContextType>) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authContextValue as AuthContextType}>
        <I18nextProvider i18n={i18n}>
          <ProfilesPage />
        </I18nextProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('ProfilesPage', () => {
  beforeEach(() => {
    mockUseProfiles.mockReturnValue({ data: mockProfilesData, isLoading: false, isError: false });
    mockUseCreateProfile.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({}) });
    mockUseUpdateProfile.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({}) });
    mockUseDeleteProfile.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({}) });
    (ProfileCreateForm as jest.Mock).mockClear();
  });

  it('renders the profiles table with mock data', () => {
    renderProfilesPage({ user: { account_type: 'individual' } });
    expect(screen.getByText('Test Profile 1')).toBeInTheDocument();
    expect(screen.getByText('Test Profile 2')).toBeInTheDocument();
    expect(screen.getByText('Personal')).toBeInTheDocument(); // From profile_type 'personal'
    expect(screen.getByText('Agency')).toBeInTheDocument(); // From profile_type 'agency'
  });

  describe('Individual User View', () => {
    const authContextIndividual = { user: { id: 'user-individual-123', account_type: 'individual', email: 'ind@test.com', username: 'induser' } };

    it('shows "Create Profile" button text for individual user', () => {
      renderProfilesPage(authContextIndividual);
      expect(screen.getByRole('button', { name: /Create Profile/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Add New Profile/i })).not.toBeInTheDocument();
    });

    it('passes correct userAccountType prop to ProfileCreateForm for individual user when modal opens', () => {
      renderProfilesPage(authContextIndividual);
      fireEvent.click(screen.getByRole('button', { name: /Create Profile/i }));
      expect(ProfileCreateForm).toHaveBeenCalledWith(
        expect.objectContaining({
          userAccountType: 'individual',
        }),
        expect.anything()
      );
    });
  });

  describe('Agency User View', () => {
    const authContextAgency = { user: { id: 'user-agency-123', account_type: 'agency', email: 'agency@test.com', username: 'agencyuser' } };
    
    it('shows "Add New Profile" button text for agency user', () => {
      renderProfilesPage(authContextAgency);
      expect(screen.getByRole('button', { name: /Add New Profile/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Create Profile/i })).not.toBeInTheDocument();
    });

    it('passes correct userAccountType prop to ProfileCreateForm for agency user when modal opens', () => {
      renderProfilesPage(authContextAgency);
      fireEvent.click(screen.getByRole('button', { name: /Add New Profile/i }));
      expect(ProfileCreateForm).toHaveBeenCalledWith(
        expect.objectContaining({
          userAccountType: 'agency',
        }),
        expect.anything()
      );
    });
  });

  it('opens create modal when "Create Profile" (or variant) button is clicked', () => {
    renderProfilesPage({ user: { account_type: 'individual' } });
    fireEvent.click(screen.getByRole('button', { name: /Create Profile/i }));
    // Check if the mocked form is rendered (which means the dialog is open)
    expect(screen.getByTestId('profile-create-form')).toBeInTheDocument();
    // Check if the modal title for "Create" is there
    expect(screen.getByText('Create New Profile', { selector: 'h2' })).toBeInTheDocument();
  });

  it('opens edit modal when an edit action is clicked', () => {
    renderProfilesPage({ user: { account_type: 'individual' } });
    // Open the first dropdown menu
    const dropdownTriggers = screen.getAllByRole('button', { name: /Open menu for/i });
    fireEvent.click(dropdownTriggers[0]);
    
    // Click the "Edit Profile" item
    fireEvent.click(screen.getByText(/Edit Profile/i));

    expect(screen.getByTestId('profile-create-form')).toBeInTheDocument();
    expect(screen.getByText('Edit Profile', { selector: 'h2' })).toBeInTheDocument();
     expect(ProfileCreateForm).toHaveBeenCalledWith(
        expect.objectContaining({
          initialData: expect.objectContaining({ name: 'Test Profile 1' }),
          userAccountType: 'individual'
        }),
        expect.anything()
      );
  });
});
