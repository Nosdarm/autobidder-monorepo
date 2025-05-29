import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

import ProfileCreateForm, { ProfileFormValues } from '../ProfileCreateForm';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, string | number>) => {
      if (params) {
        let translation = key;
        // Basic placeholder replacement for {{param}} or {param}
        for (const pKey in params) {
          translation = translation.replace(new RegExp(`{{${pKey}}}|{${pKey}}`, 'g'), String(params[pKey]));
        }
        return translation;
      }
      return key;
    },
    i18n: {
      changeLanguage: vi.fn(),
      language: 'en',
    },
  }),
}));

// Mock lucide-react for Loader2 icon if needed for assertions,
// or ensure tests don't strictly depend on its specific DOM structure.
vi.mock('lucide-react', async () => {
  const actual = await vi.importActual('lucide-react');
  return {
    ...actual,
    Loader2: () => <svg data-testid="loader-icon" />,
  };
});


describe('ProfileCreateForm Component', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    onSave: mockOnSave,
    onCancel: mockOnCancel,
    isSaving: false,
    initialData: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderForm = (props?: Partial<typeof defaultProps>) => {
    return render(<ProfileCreateForm {...defaultProps} {...props} />);
  };

  test('renders correctly with default values', () => {
    renderForm();

    // Check for presence of all form fields using their labels (as per i18n keys)
    expect(screen.getByLabelText('profileForm.nameLabel')).toBeInTheDocument();
    expect(screen.getByLabelText('profileForm.nameLabel')).toHaveValue('');

    // Shadcn Select: Trigger has the role 'combobox' and is associated with the label
    expect(screen.getByRole('combobox', { name: 'profileForm.typeLabel' })).toBeInTheDocument();
    // Default placeholder for type should be visible. The actual SelectValue component might render the placeholder.
    expect(screen.getByText('profileForm.typePlaceholder')).toBeInTheDocument();


    expect(screen.getByLabelText('profileForm.skillsLabel')).toBeInTheDocument();
    expect(screen.getByLabelText('profileForm.skillsLabel')).toHaveValue('');
    
    expect(screen.getByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).toBeInTheDocument();
    expect(screen.getByText('profileForm.experienceLevelPlaceholder')).toBeInTheDocument();

    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).not.toBeChecked();

    // Check for buttons
    expect(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'profileForm.cancelButton' })).toBeInTheDocument();
  });

  test('renders correctly with initialData (edit mode)', () => {
    const initialData: ProfileFormValues = {
      id: '123',
      name: 'Test User',
      type: 'agency',
      autobidEnabled: true,
      skills: ['React', 'Node.js'],
      experience_level: 'expert',
    };
    renderForm({ initialData });

    expect(screen.getByLabelText('profileForm.nameLabel')).toHaveValue(initialData.name);
    
    // For Select, check if the selected value is displayed
    // The text for the selected value is based on the i18n key for that value.
    expect(screen.getByText('profileForm.typeAgency')).toBeInTheDocument(); // 'agency' maps to this key
    
    expect(screen.getByLabelText('profileForm.skillsLabel')).toHaveValue(initialData.skills!.join(', '));
    
    expect(screen.getByText('profileForm.experienceExpert')).toBeInTheDocument(); // 'expert' maps to this key

    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).toBeChecked();
    
    // Submit button text should change in edit mode
    expect(screen.getByRole('button', { name: 'profileForm.saveButtonUpdate' })).toBeInTheDocument();
  });

  describe('Validation Logic', () => {
    test('name field: required validation', async () => {
      renderForm();
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      // FormMessage for name field should display the error
      const nameFormItem = screen.getByLabelText('profileForm.nameLabel').closest('div[role="group"]'); // Heuristic, might need better selector
      if (!nameFormItem) throw new Error("Could not find FormItem for name");
      
      await waitFor(() => {
        expect(within(nameFormItem).getByText('profileForm.validation.nameRequired')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    test('name field: minLength validation', async () => {
      renderForm();
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: 'a' } });
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      const nameFormItem = screen.getByLabelText('profileForm.nameLabel').closest('div[role="group"]');
      if (!nameFormItem) throw new Error("Could not find FormItem for name");

      await waitFor(() => {
        // The t mock will replace {min} with the value
        expect(within(nameFormItem).getByText('profileForm.validation.nameMinLength_min_3')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    test('type field: required validation', async () => {
      renderForm();
      // Fill name to pass its validation
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: 'Valid Name' } });
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      // FormMessage for type field
      // For shadcn Select, the FormItem is usually a parent of the combobox role.
      const typeSelect = screen.getByRole('combobox', { name: 'profileForm.typeLabel' });
      const typeFormItem = typeSelect.closest('div[role="group"]');
      if (!typeFormItem) throw new Error("Could not find FormItem for type");

      await waitFor(() => {
        expect(within(typeFormItem).getByText('profileForm.validation.typeRequired')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });
  });

  describe('Submission Logic', () => {
    const validFormData: ProfileFormValues = {
      name: 'Valid Profile Name',
      type: 'personal',
      autobidEnabled: true,
      skills: ['React', 'TypeScript', 'Node.js'],
      experience_level: 'intermediate',
    };

    test('calls onSave with correct data on valid submission (create mode)', async () => {
      renderForm();

      // Fill name
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: validFormData.name } });

      // Select type
      fireEvent.click(screen.getByRole('combobox', { name: 'profileForm.typeLabel' }));
      await screen.findByText('profileForm.typePersonal'); // Wait for options
      fireEvent.click(screen.getByText('profileForm.typePersonal'));

      // Fill skills
      fireEvent.change(screen.getByLabelText('profileForm.skillsLabel'), { target: { value: validFormData.skills!.join(', ') } });
      
      // Select experience level
      fireEvent.click(screen.getByRole('combobox', { name: 'profileForm.experienceLevelLabel' }));
      await screen.findByText('profileForm.experienceIntermediate'); // Wait for options
      fireEvent.click(screen.getByText('profileForm.experienceIntermediate'));

      // Toggle autobid switch
      fireEvent.click(screen.getByRole('switch', { name: 'profileForm.autobidLabel' }));

      // Submit
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledTimes(1);
        // For create, 'id' is not part of the form data sent, it's generated by backend or not present
        const { id, ...expectedData } = validFormData;
        expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining(expectedData));
      });
    });
    
    test('calls onSave with correct data including ID on valid submission (edit mode)', async () => {
      const initialData: ProfileFormValues = {
        id: 'test-id-123',
        name: 'Old Name',
        type: 'agency',
        autobidEnabled: false,
        skills: ['OldSkill'],
        experience_level: 'entry',
      };
      renderForm({ initialData });

      // Modify some fields
      const newName = "New Updated Name";
      const newSkills = "UpdatedSkill1, UpdatedSkill2";
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: newName } });
      fireEvent.change(screen.getByLabelText('profileForm.skillsLabel'), { target: { value: newSkills } });
      // Toggle autobid
      fireEvent.click(screen.getByRole('switch', { name: 'profileForm.autobidLabel' }));


      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonUpdate' }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledTimes(1);
        expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
          id: initialData.id,
          name: newName,
          type: initialData.type, // Type wasn't changed in this specific interaction
          autobidEnabled: true, // Toggled from false
          skills: ["UpdatedSkill1", "UpdatedSkill2"],
          experience_level: initialData.experience_level, // Exp level not changed
        }));
      });
    });

    test('skills are correctly parsed (with spaces and empty values)', async () => {
      renderForm();
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: 'Skills Test Profile' } });
      fireEvent.click(screen.getByRole('combobox', { name: 'profileForm.typeLabel' }));
      await screen.findByText('profileForm.typePersonal');
      fireEvent.click(screen.getByText('profileForm.typePersonal'));

      fireEvent.change(screen.getByLabelText('profileForm.skillsLabel'), { target: { value: '  React  ,Node.js,,  Python  , ' } });
      
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            skills: ['React', 'Node.js', 'Python'],
          })
        );
      });
    });


    test('disables submit button and shows spinner when isSaving is true', () => {
      renderForm({ isSaving: true });
      const submitButton = screen.getByRole('button', { name: 'profileForm.saveButtonCreate' });
      expect(submitButton).toBeDisabled();
      expect(within(submitButton).getByTestId('loader-icon')).toBeInTheDocument();
    });
  });

  describe('Cancel Logic', () => {
    test('calls onCancel when cancel button is clicked', () => {
      renderForm();
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.cancelButton' }));
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });
});
