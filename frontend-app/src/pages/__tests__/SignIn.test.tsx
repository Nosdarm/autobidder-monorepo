import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, Mock } from 'vitest'; // Changed from 'vitest' to specific 'Mock' for type assertion

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the api module
vi.mock('../../lib/axios', () => ({
  default: {
    post: vi.fn(),
  },
}));
// Import api after the mock
import api from '../../lib/axios';

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }), // Mock setItem
    removeItem: vi.fn((key: string) => { delete store[key]; }), // Mock removeItem
    clear: vi.fn(() => { store = {}; }), // Mock clear
  };
})();
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Import the component after all mocks are set up
import SignIn from '../SignIn';

describe('SignIn Component', () => {
  const mockApiPost = api.post as Mock; // Type assertion for mocked api.post

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear(); // Clear localStorage mock before each test
  });

  test('Successful Login', async () => {
    mockApiPost.mockResolvedValueOnce({ data: { access_token: 'fake-token' } });

    render(<SignIn />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Войти'));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/auth/login", { email: 'test@example.com', password: 'password123' }));
    await waitFor(() => expect(localStorage.setItem).toHaveBeenCalledWith('token', 'fake-token'));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/dashboard'));
  });

  test('Login Failure (Invalid Credentials)', async () => {
    mockApiPost.mockRejectedValueOnce({ 
      isAxiosError: true, // Simulate AxiosError structure
      response: { data: { detail: 'Invalid credentials' } } 
    });

    render(<SignIn />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'wrong@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByText('Войти'));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('Invalid credentials')).toBeInTheDocument());
    expect(localStorage.setItem).not.toHaveBeenCalledWith('token', expect.any(String));
    expect(mockNavigate).not.toHaveBeenCalledWith('/dashboard');
  });

  test('Client-side validation: invalid email format', async () => {
    render(<SignIn />);
    
    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'invalid-email' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Войти'));

    // Check for error message without waiting for API call
    expect(screen.getByText('Введите корректный email.')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  test('Client-side validation: short password', async () => {
    render(<SignIn />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'pass' } }); // Short password
    fireEvent.click(screen.getByText('Войти'));

    expect(screen.getByText('Пароль должен быть не менее 8 символов.')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });
});
