import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, Mock } from 'vitest';

// Mock react-router-dom's useNavigate (Navbar uses it)
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    // Mock Link if it causes issues, or ensure Navbar is shallowly rendered if not testing its links
    Link: ({ children, to }: { children: React.ReactNode, to: string }) => <a href={to}>{children}</a>,
  };
});

// Mock the api module
// Adjusted path assuming Profile.tsx is in src/pages/ and lib/axios.ts is in src/lib/
vi.mock('../../lib/axios', () => ({ 
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));
import api from '../../lib/axios'; // Adjusted path

// Mock localStorage (Navbar uses it)
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Mock Navbar to simplify Profile.tsx tests
vi.mock('../../components/Navbar', () => ({ // Adjusted path
  default: () => <nav data-testid="mock-navbar">Mock Navbar</nav>,
}));

// Import the component after all mocks are set up
import ProfilePage from '../Profile';

describe('ProfilePage Component', () => {
  const mockApiGet = api.get as Mock;
  const mockApiPost = api.post as Mock;
  const mockApiDelete = api.delete as Mock;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear(); // Clear localStorage mock before each test
  });

  // Helper function to create mock profiles
  const createMockProfile = (id: string, name: string, type: "personal" | "agency" = "personal", autobid_enabled = false) => ({
    id,
    name,
    profile_type: type,
    autobid_enabled,
    user_id: 'test-user-id', // Assuming a consistent user_id for tests
  });

  test('Test Initial Profile Fetching and Display', async () => {
    const mockProfileData = [createMockProfile('1', 'Test Profile 1', 'personal', true)];
    mockApiGet.mockResolvedValueOnce({ data: mockProfileData });

    render(<ProfilePage />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/profiles/me"));
    
    await waitFor(() => {
      expect(screen.getByText('Test Profile 1')).toBeInTheDocument();
      expect(screen.getByText('(personal)')).toBeInTheDocument();
      expect(screen.getByText('Autobid ON')).toBeInTheDocument(); // Test for autobid display
    });
  });

  test('Test Creating a New Profile', async () => {
    mockApiGet.mockResolvedValueOnce({ data: [] }); // Initial empty list
    const newProfileName = 'New Awesome Profile';
    const newProfileType = 'agency';
    const createdProfile = createMockProfile('2', newProfileName, newProfileType);
    
    mockApiPost.mockResolvedValueOnce({ data: createdProfile }); 
    mockApiGet.mockResolvedValueOnce({ data: [createdProfile] }); // For refresh

    render(<ProfilePage />);

    const nameInput = screen.getByPlaceholderText('Название') as HTMLInputElement;
    const typeSelect = screen.getByRole('combobox') as HTMLSelectElement; // More robust selector for select
    const createButton = screen.getByText('Создать');

    fireEvent.change(nameInput, { target: { value: newProfileName } });
    fireEvent.change(typeSelect, { target: { value: newProfileType } });
    fireEvent.click(createButton);

    await waitFor(() => 
      expect(api.post).toHaveBeenCalledWith("/profiles", { name: newProfileName, profile_type: newProfileType })
    );
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2)); // Initial fetch + refresh
    
    await waitFor(() => {
      expect(screen.getByText(newProfileName)).toBeInTheDocument();
      expect(screen.getByText(`(${newProfileType})`)).toBeInTheDocument();
    });

    // Assert input fields are cleared
    expect(nameInput.value).toBe('');
    expect(typeSelect.value).toBe('personal'); // Assuming it resets to default
  });

  test('Test Deleting a Profile', async () => {
    const profiles = [
      createMockProfile('1', 'To Delete Profile'),
      createMockProfile('2', 'To Keep Profile')
    ];
    mockApiGet.mockResolvedValueOnce({ data: profiles }); // Initial load
    mockApiDelete.mockResolvedValueOnce({}); // Delete success
    mockApiGet.mockResolvedValueOnce({ data: [profiles[1]] }); // Load after delete

    render(<ProfilePage />);

    await waitFor(() => expect(screen.getByText('To Delete Profile')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('To Keep Profile')).toBeInTheDocument());

    // Find the delete button for "To Delete Profile"
    // This assumes the profile name is within the same list item as the button
    const profileToDeleteRow = screen.getByText('To Delete Profile').closest('li');
    if (!profileToDeleteRow) throw new Error("Could not find list item for 'To Delete Profile'");
    
    const deleteButton = within(profileToDeleteRow).getByRole('button', { name: /удалить/i });
    fireEvent.click(deleteButton);

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith("/profiles/1"));
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2)); // Initial fetch + refresh
    
    await waitFor(() => {
      expect(screen.queryByText('To Delete Profile')).not.toBeInTheDocument();
      expect(screen.getByText('To Keep Profile')).toBeInTheDocument();
    });
  });

  test('Test Error Handling on Profile Creation Failure', async () => {
    mockApiGet.mockResolvedValueOnce({ data: [] }); // Initial load
    const errorMessage = 'Creation failed due to server error';
    mockApiPost.mockRejectedValueOnce({ 
      isAxiosError: true, // To be properly handled by the component's catch block
      response: { data: { detail: errorMessage } } 
    });

    render(<ProfilePage />);

    const nameInput = screen.getByPlaceholderText('Название');
    const createButton = screen.getByText('Создать');

    fireEvent.change(nameInput, { target: { value: 'Fail Profile' } });
    fireEvent.click(createButton);

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    
    // The component sets error to "Ошибка создания профиля. Пожалуйста, попробуйте снова."
    // or specific message if logic is updated to pass it through.
    // Based on current component logic, it's a generic message.
    await waitFor(() => expect(screen.getByText('Ошибка создания профиля. Пожалуйста, попробуйте снова.')).toBeInTheDocument());
  });

  test('Test Error Handling on Profile Fetching Failure', async () => {
    const errorMessage = 'Failed to fetch profiles';
    mockApiGet.mockRejectedValueOnce({ 
      isAxiosError: true,
      response: { data: { detail: errorMessage } } 
    });

    render(<ProfilePage />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/profiles/me"));
    await waitFor(() => expect(screen.getByText('Ошибка загрузки профилей. Пожалуйста, попробуйте позже.')).toBeInTheDocument());
  });
});
