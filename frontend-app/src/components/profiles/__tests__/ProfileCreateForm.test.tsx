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
    userAccountType: 'individual' as 'individual' | 'agency', // Add userAccountType
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderForm = (props?: Partial<typeof defaultProps>) => {
    // Ensure userAccountType is always provided, defaulting if necessary
    const mergedProps = { ...defaultProps, ...props };
    if (!mergedProps.userAccountType) {
      mergedProps.userAccountType = 'individual'; 
    }
    return render(<ProfileCreateForm {...mergedProps} />);
  };

  test('renders correctly with default values for individual user', () => {
    renderForm({ userAccountType: 'individual' });

    expect(screen.getByLabelText('profileForm.nameLabel')).toBeInTheDocument();
    // For an individual user, type field should NOT be visible, and skills/experience ARE visible
    expect(screen.queryByRole('combobox', { name: 'profileForm.typeLabel' })).not.toBeInTheDocument();
    
    expect(screen.getByLabelText('profileForm.skillsLabel')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).toBeInTheDocument();
    expect(screen.queryByLabelText('profileForm.agencySpecificFieldLabel')).not.toBeInTheDocument();

    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).toBeInTheDocument();
    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).not.toBeChecked();
    expect(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' })).toBeInTheDocument();
  });
  
  test('renders correctly with initialData for individual user (edit mode, type is personal)', () => {
    const initialData: ProfileFormValues = {
      id: '123', name: 'Test User', type: 'personal', autobidEnabled: true,
      skills: ['React', 'Node.js'], experience_level: 'expert',
    };
    renderForm({ initialData, userAccountType: 'individual' });

    expect(screen.getByLabelText('profileForm.nameLabel')).toHaveValue(initialData.name);
    // Type field still not visible for individual user, even in edit mode.
    expect(screen.queryByRole('combobox', { name: 'profileForm.typeLabel' })).not.toBeInTheDocument();
    
    expect(screen.getByLabelText('profileForm.skillsLabel')).toHaveValue(initialData.skills!.join(', '));
    expect(screen.getByText('profileForm.experienceExpert')).toBeInTheDocument(); // 'expert' maps to this key
    expect(screen.queryByLabelText('profileForm.agencySpecificFieldLabel')).not.toBeInTheDocument();
    
    expect(screen.getByRole('switch', { name: 'profileForm.autobidLabel' })).toBeChecked();
    expect(screen.getByRole('button', { name: 'profileForm.saveButtonUpdate' })).toBeInTheDocument();
  });


  // New tests for conditional rendering based on userAccountType and selected profile_type
  describe('Individual User (userAccountType="individual")', () => {
    const userAccountType = 'individual';

    test('Profile Type select is NOT visible', () => {
      renderForm({ userAccountType });
      expect(screen.queryByRole('combobox', { name: 'profileForm.typeLabel' })).not.toBeInTheDocument();
    });

    test('Skills and Experience Level fields ARE visible by default', () => {
      renderForm({ userAccountType });
      expect(screen.getByLabelText('profileForm.skillsLabel')).toBeVisible();
      expect(screen.getByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).toBeVisible();
    });

    test('Agency Specific Field is NOT visible', () => {
      renderForm({ userAccountType });
      expect(screen.queryByLabelText('profileForm.agencySpecificFieldLabel')).not.toBeInTheDocument();
    });
  });

  describe('Agency User (userAccountType="agency")', () => {
    const userAccountType = 'agency';

    test('Profile Type select IS visible', () => {
      renderForm({ userAccountType });
      expect(screen.getByRole('combobox', { name: 'profileForm.typeLabel' })).toBeVisible();
    });

    test('When "personal" is selected as profile type: Skills and Experience ARE visible, Agency Specific is NOT', async () => {
      renderForm({ userAccountType });
      const typeSelect = screen.getByRole('combobox', { name: 'profileForm.typeLabel' });
      fireEvent.click(typeSelect);
      await screen.findByText('profileForm.typePersonal'); // Wait for options
      fireEvent.click(screen.getByText('profileForm.typePersonal'));

      await waitFor(() => {
        expect(screen.getByLabelText('profileForm.skillsLabel')).toBeVisible();
        expect(screen.getByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).toBeVisible();
        expect(screen.queryByLabelText('profileForm.agencySpecificFieldLabel')).not.toBeInTheDocument();
      });
    });
    
    test('When "agency" is selected as profile type: Skills and Experience are NOT visible, Agency Specific IS visible', async () => {
      renderForm({ userAccountType });
      const typeSelect = screen.getByRole('combobox', { name: 'profileForm.typeLabel' });
      fireEvent.click(typeSelect);
      await screen.findByText('profileForm.typeAgency');
      fireEvent.click(screen.getByText('profileForm.typeAgency'));

      await waitFor(() => {
        expect(screen.queryByLabelText('profileForm.skillsLabel')).not.toBeInTheDocument();
        expect(screen.queryByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).not.toBeInTheDocument();
        expect(screen.getByLabelText('profileForm.agencySpecificFieldLabel')).toBeVisible();
      });
    });
    
    test('renders correctly with initialData (edit mode, type is agency)', () => {
      const initialData: ProfileFormValues = {
        id: '123', name: 'Agency Test', type: 'agency', autobidEnabled: false,
      };
      renderForm({ initialData, userAccountType: 'agency' });
      expect(screen.getByLabelText('profileForm.nameLabel')).toHaveValue(initialData.name);
      expect(screen.getByText('profileForm.typeAgency')).toBeInTheDocument(); // Selected type visible
      // Skills and Experience should not be visible for agency type
      expect(screen.queryByLabelText('profileForm.skillsLabel')).not.toBeInTheDocument();
      expect(screen.queryByRole('combobox', { name: 'profileForm.experienceLevelLabel' })).not.toBeInTheDocument();
      // Agency specific field should be visible
      expect(screen.getByLabelText('profileForm.agencySpecificFieldLabel')).toBeVisible();
    });
  });

  // --- Re-integrating existing Validation and Submission tests, ensuring they pass with new structure ---
  describe('Validation Logic (with userAccountType considerations)', () => {
    test('name field: required validation', async () => {
      renderForm({ userAccountType: 'individual' }); // Test with one type, should be same for both
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      const nameFormItem = screen.getByLabelText('profileForm.nameLabel').closest('div[role="group"]');
      if (!nameFormItem) throw new Error("Could not find FormItem for name");
      
      await waitFor(() => {
        expect(within(nameFormItem).getByText('profileForm.validation.nameRequired')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    test('name field: minLength validation', async () => {
      renderForm({ userAccountType: 'individual' });
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: 'a' } });
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      const nameFormItem = screen.getByLabelText('profileForm.nameLabel').closest('div[role="group"]');
      if (!nameFormItem) throw new Error("Could not find FormItem for name");

      await waitFor(() => {
        expect(within(nameFormItem).getByText('profileForm.validation.nameMinLength_min_3')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    // Type validation is only relevant for agency users as it's visible
    test('type field: required validation (for agency user)', async () => {
      renderForm({ userAccountType: 'agency' });
      fireEvent.change(screen.getByLabelText('profileForm.nameLabel'), { target: { value: 'Valid Name' } });
      // Do not select a type
      fireEvent.click(screen.getByRole('button', { name: 'profileForm.saveButtonCreate' }));
      
      const typeSelect = screen.getByRole('combobox', { name: 'profileForm.typeLabel' });
      const typeFormItem = typeSelect.closest('div[role="group"]');
      if (!typeFormItem) throw new Error("Could not find FormItem for type");

      await waitFor(() => {
        expect(within(typeFormItem).getByText('profileForm.validation.typeRequired')).toBeInTheDocument();
      });
      expect(mockOnSave).not.toHaveBeenCalled();
    });
  });

  describe('Submission Logic (with userAccountType considerations)', () => {
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
