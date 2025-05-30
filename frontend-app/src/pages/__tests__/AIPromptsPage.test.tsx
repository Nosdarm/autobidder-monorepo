import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AIPromptsPage from '../AIPromptsPage';
import i18n from '@/i18n'; // Your i18n configuration

const queryClient = new QueryClient();

// Mock alert
global.alert = jest.fn();

const renderAIPromptsPage = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        <AIPromptsPage />
      </I18nextProvider>
    </QueryClientProvider>
  );
};

describe('AIPromptsPage', () => {
  beforeEach(() => {
    // Reset alert mock before each test
    (global.alert as jest.Mock).mockClear();
    renderAIPromptsPage();
  });

  it('renders the page title, table, and "Create New Prompt" button', () => {
    expect(screen.getByText('aiPromptsPage.title')).toBeInTheDocument();
    expect(screen.getByText('aiPromptsPage.description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'aiPromptsPage.createButton' })).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('aiPromptsPage.table.caption')).toBeInTheDocument();
  });

  it('displays mock AI prompts in the table', () => {
    // Check for a couple of mock prompts by name
    expect(screen.getByText('Blog Post Idea Generator')).toBeInTheDocument();
    expect(screen.getByText('Code Explainer')).toBeInTheDocument();
    // Check for categories
    expect(screen.getAllByText('Marketing').length).toBeGreaterThanOrEqual(1); // Category of "Blog Post Idea Generator"
    expect(screen.getAllByText('Technical').length).toBeGreaterThanOrEqual(1); // Category of "Code Explainer"
    // Check for action buttons (via dropdown)
    const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for/i });
    expect(dropdownTriggers.length).toBeGreaterThan(0); 
  });

  describe('Create New Prompt Dialog', () => {
    it('opens "Create New Prompt" dialog when button is clicked', () => {
      fireEvent.click(screen.getByRole('button', { name: 'aiPromptsPage.createButton' }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('aiPromptsPage.createModal.title')).toBeInTheDocument();
      expect(screen.getByLabelText('aiPromptsPage.form.nameLabel')).toBeInTheDocument();
      expect(screen.getByLabelText('aiPromptsPage.form.categoryLabel')).toBeInTheDocument(); // SelectTrigger
      expect(screen.getByLabelText('aiPromptsPage.form.promptTextLabel')).toBeInTheDocument();
    });

    it('allows filling the create prompt form and simulates saving', async () => {
      fireEvent.click(screen.getByRole('button', { name: 'aiPromptsPage.createButton' }));

      const nameInput = screen.getByLabelText('aiPromptsPage.form.nameLabel');
      const categorySelectTrigger = screen.getByLabelText('aiPromptsPage.form.categoryLabel');
      const promptTextInput = screen.getByLabelText('aiPromptsPage.form.promptTextLabel');

      fireEvent.change(nameInput, { target: { value: 'New Test Prompt' } });
      
      fireEvent.mouseDown(categorySelectTrigger);
      // Select an option (e.g., General)
      await screen.findByText('aiPromptsPage.form.categoryOptions.general');
      fireEvent.click(screen.getByText('aiPromptsPage.form.categoryOptions.general'));
      
      fireEvent.change(promptTextInput, { target: { value: 'This is the prompt text.' } });

      fireEvent.click(screen.getByRole('button', { name: 'aiPromptsPage.form.saveButton' }));

      expect(global.alert).toHaveBeenCalledWith('Mock: Prompt "New Test Prompt" saved successfully!');
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      // Verify the new prompt appears in the table (due to local state update)
      expect(screen.getByText('New Test Prompt')).toBeInTheDocument();
    });
  });

  describe('Edit Prompt Dialog', () => {
    it('opens "Edit AI Prompt" dialog when an edit action is clicked', async () => {
      // Open the first dropdown menu (for "Blog Post Idea Generator")
      const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for Blog Post Idea Generator/i });
      fireEvent.click(dropdownTriggers[0]);
      
      // Click the "Edit" item
      const editButton = await screen.findByText('common.edit');
      fireEvent.click(editButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('aiPromptsPage.editModal.title')).toBeInTheDocument();
      
      // Check if form is pre-filled
      expect(screen.getByLabelText('aiPromptsPage.form.nameLabel')).toHaveValue('Blog Post Idea Generator');
      // For select, check if the current value is displayed (implementation specific)
      // The text for the selected value is based on the i18n key for that value.
      expect(screen.getByText('aiPromptsPage.form.categoryOptions.marketing')).toBeInTheDocument();
      expect(screen.getByLabelText('aiPromptsPage.form.promptTextLabel')).toHaveValue('Generate 5 blog post ideas for a company that sells eco-friendly dog toys...');
    });

    it('allows editing and simulates saving', async () => {
      const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for Blog Post Idea Generator/i });
      fireEvent.click(dropdownTriggers[0]);
      const editButton = await screen.findByText('common.edit');
      fireEvent.click(editButton);

      const nameInput = screen.getByLabelText('aiPromptsPage.form.nameLabel');
      fireEvent.change(nameInput, { target: { value: 'Updated Blog Post Ideas' } });
      fireEvent.click(screen.getByRole('button', { name: 'aiPromptsPage.form.saveButton' }));
      
      expect(global.alert).toHaveBeenCalledWith('Mock: Prompt "Updated Blog Post Ideas" saved successfully!');
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      expect(screen.getByText('Updated Blog Post Ideas')).toBeInTheDocument();
      expect(screen.queryByText('Blog Post Idea Generator')).not.toBeInTheDocument(); // Old name should be gone
    });
  });

  describe('Delete Prompt Alert Dialog', () => {
    it('opens "Confirm Deletion" alert when a delete action is clicked', async () => {
      const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for Code Explainer/i });
      fireEvent.click(dropdownTriggers[0]); // Using the second prompt for this test
      
      const deleteButton = await screen.findByText('common.delete');
      fireEvent.click(deleteButton);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      expect(screen.getByText('aiPromptsPage.deleteAlert.title')).toBeInTheDocument();
      // Check if the description contains the prompt name
      const alertDescription = screen.getByText((content, element) => {
        // Check if the text content of the element contains the expected substring
        // This is a bit flexible to handle potential variations in the full translated string
        return content.startsWith('aiPromptsPage.deleteAlert.description') && content.includes('Code Explainer');
      });
      expect(alertDescription).toBeInTheDocument();
    });

    it('simulates deleting a prompt after confirmation', async () => {
      const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for Code Explainer/i });
      fireEvent.click(dropdownTriggers[0]);
      const deleteButton = await screen.findByText('common.delete');
      fireEvent.click(deleteButton);

      fireEvent.click(screen.getByRole('button', { name: 'common.confirmDeleteButton' }));
      
      expect(global.alert).toHaveBeenCalledWith('Mock: Prompt "Code Explainer" deletion initiated!');
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      // Verify the prompt is removed from the table (due to local state update)
      expect(screen.queryByText('Code Explainer')).not.toBeInTheDocument();
    });

    it('closes alert dialog when cancel is clicked', async () => {
      const dropdownTriggers = screen.getAllByRole('button', { name: /Actions for Code Explainer/i });
      fireEvent.click(dropdownTriggers[0]);
      const deleteButton = await screen.findByText('common.delete');
      fireEvent.click(deleteButton);

      fireEvent.click(screen.getByRole('button', { name: 'common.cancel' }));
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      expect(screen.getByText('Code Explainer')).toBeInTheDocument(); // Still there
    });
  });
});
