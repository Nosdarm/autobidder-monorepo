import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, Mock } from 'vitest';

// Mock react-router-dom's useNavigate (though not used by SignUp, good for consistency)
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
import api from '../../lib/axios';

// Mock window.alert
global.alert = vi.fn();

// Import the component after all mocks are set up
import SignUp from '../SignUp';

describe('SignUp Component', () => {
  const mockApiPost = api.post as Mock;

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset any component-specific state if SignUp component itself holds global state
    // For this component, clearing mocks is the primary concern.
  });

  test('Successful Registration', async () => {
    mockApiPost.mockResolvedValueOnce({ 
      data: { message: "Регистрация успешна. Проверьте вашу почту для верификации." } 
    });

    render(<SignUp />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'password123' } });
    fireEvent.change(screen.getByPlaceholderText('Повторите пароль'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Зарегистрироваться'));

    await waitFor(() => 
      expect(api.post).toHaveBeenCalledWith("/auth/register", { email: 'test@example.com', password: 'password123' })
    );
    await waitFor(() => 
      expect(screen.getByText("Регистрация успешна. Проверьте вашу почту для верификации.")).toBeInTheDocument()
    );

    // Check if form fields are cleared
    expect((screen.getByPlaceholderText('Эл. почта') as HTMLInputElement).value).toBe('');
    expect((screen.getByPlaceholderText('Пароль') as HTMLInputElement).value).toBe('');
    expect((screen.getByPlaceholderText('Повторите пароль') as HTMLInputElement).value).toBe('');
  });

  test('Registration Failure (Email already exists)', async () => {
    const errorMessage = 'Email already registered';
    mockApiPost.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: errorMessage } }
    });

    render(<SignUp />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'existing@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'password123' } });
    fireEvent.change(screen.getByPlaceholderText('Повторите пароль'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Зарегистрироваться'));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText(errorMessage)).toBeInTheDocument());
  });

  test('Password Mismatch (Client-side)', async () => {
    render(<SignUp />);

    fireEvent.change(screen.getByPlaceholderText('Эл. почта'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Пароль'), { target: { value: 'password123' } });
    fireEvent.change(screen.getByPlaceholderText('Повторите пароль'), { target: { value: 'password456' } }); // Mismatched password
    fireEvent.click(screen.getByText('Зарегистрироваться'));

    // The component uses alert for password mismatch
    expect(global.alert).toHaveBeenCalledWith("Пароли не совпадают");
    expect(api.post).not.toHaveBeenCalled();
  });
});
