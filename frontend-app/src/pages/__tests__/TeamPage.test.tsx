import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TeamPage from '../TeamPage';
import { AuthContext, AuthContextType, User } from '@/contexts/AuthContext';
import i18n from '@/i18n'; // Your i18n configuration

const queryClient = new QueryClient();

// Mock alert
global.alert = jest.fn();

const renderTeamPage = (authContextValue: Partial<AuthContextType>) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authContextValue as AuthContextType}>
        <I18nextProvider i18n={i18n}>
          <TeamPage />
        </I18nextProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('TeamPage', () => {
  describe('Access Control', () => {
    it('shows "Access Denied" message for individual users', () => {
      const individualUser: User = { id: 'ind-1', username: 'indUser', email: 'ind@test.com', account_type: 'individual' };
      renderTeamPage({ user: individualUser });
      expect(screen.getByText('teamPage.accessDenied.title')).toBeInTheDocument();
      expect(screen.getByText('teamPage.accessDenied.description')).toBeInTheDocument();
      expect(screen.queryByText('teamPage.title')).not.toBeInTheDocument();
    });

    it('shows "Access Denied" message if user is not authenticated (null user)', () => {
      renderTeamPage({ user: null });
      expect(screen.getByText('teamPage.accessDenied.title')).toBeInTheDocument();
      expect(screen.getByText('teamPage.accessDenied.description')).toBeInTheDocument();
    });

    it('shows team management UI for agency users', () => {
      const agencyUser: User = { id: 'agn-1', username: 'agnUser', email: 'agn@test.com', account_type: 'agency' };
      renderTeamPage({ user: agencyUser });
      expect(screen.getByText('teamPage.title')).toBeInTheDocument();
      expect(screen.getByText('teamPage.description')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'teamPage.inviteButton' })).toBeInTheDocument();
      expect(screen.getByRole('table')).toBeInTheDocument();
      // Check for mock team members
      expect(screen.getByText('Alice Wonderland')).toBeInTheDocument();
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument(); // Role of Alice
    });
  });

  describe('Agency User Functionality', () => {
    const agencyUser: User = { id: 'agn-1', username: 'agnUser', email: 'agn@test.com', account_type: 'agency' };

    beforeEach(() => {
      renderTeamPage({ user: agencyUser });
    });

    it('opens "Invite New Member" dialog when button is clicked', () => {
      fireEvent.click(screen.getByRole('button', { name: 'teamPage.inviteButton' }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('teamPage.inviteModal.title')).toBeInTheDocument();
      expect(screen.getByLabelText('teamPage.inviteModal.emailLabel')).toBeInTheDocument();
      expect(screen.getByLabelText('teamPage.inviteModal.roleLabel')).toBeInTheDocument(); // This will be the trigger button for select
    });

    it('allows filling the invite member form and simulates sending invitation', () => {
      fireEvent.click(screen.getByRole('button', { name: 'teamPage.inviteButton' }));
      
      const emailInput = screen.getByLabelText('teamPage.inviteModal.emailLabel');
      const roleSelectTrigger = screen.getByLabelText('teamPage.inviteModal.roleLabel'); // Gets the SelectTrigger

      fireEvent.change(emailInput, { target: { value: 'newmember@example.com' } });
      
      // Open the select dropdown
      fireEvent.mouseDown(roleSelectTrigger); // Use mouseDown or click depending on how Select is built
      // Select an option (assuming 'Admin' is one of the options)
      // The text for options comes from i18n keys like 'teamPage.inviteModal.roleAdmin'
      fireEvent.click(screen.getByText('teamPage.inviteModal.roleAdmin')); 

      fireEvent.click(screen.getByRole('button', { name: 'teamPage.inviteModal.sendButton' }));

      expect(global.alert).toHaveBeenCalledWith('Mock: Invitation sent to newmember@example.com with role Admin');
      // Dialog should close after sending
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('displays team members in a table', () => {
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getByText('teamPage.membersTable.caption')).toBeInTheDocument();
        // Headers
        expect(screen.getByText('teamPage.membersTable.headerName')).toBeInTheDocument();
        expect(screen.getByText('teamPage.membersTable.headerEmail')).toBeInTheDocument();
        expect(screen.getByText('teamPage.membersTable.headerRole')).toBeInTheDocument();
        expect(screen.getByText('teamPage.membersTable.headerActions')).toBeInTheDocument();
        // Mock data rows
        expect(screen.getByText('Alice Wonderland')).toBeInTheDocument();
        expect(screen.getByText('alice@example.com')).toBeInTheDocument();
        expect(screen.getAllByText('Admin')[0]).toBeInTheDocument(); // Alice is Admin

        expect(screen.getByText('Bob The Builder')).toBeInTheDocument();
        expect(screen.getByText('bob@example.com')).toBeInTheDocument();
        expect(screen.getAllByText('Member')[0]).toBeInTheDocument(); // Bob is Member
        
        // Check for action buttons (they are disabled in the mock setup)
        const editButtons = screen.getAllByRole('button', { name: /common.edit/i });
        expect(editButtons.length).toBeGreaterThan(0);
        editButtons.forEach(button => expect(button).toBeDisabled());

        const removeButtons = screen.getAllByRole('button', { name: /common.delete/i }); // "Remove" is common.delete in TeamPage's context
        expect(removeButtons.length).toBeGreaterThan(0);
        removeButtons.forEach(button => expect(button).toBeDisabled());
    });
  });
});
