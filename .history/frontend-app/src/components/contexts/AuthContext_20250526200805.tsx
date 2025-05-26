import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, User, LoginCredentials, RegisterUserInfo, AuthResponse } from '@/services/authService'; // Assuming authService exports these

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userInfo: RegisterUserInfo) => Promise<void>;
  logoutContext: () => void;
  // initializeAuth is typically called internally by AuthProvider
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start with loading true

  useEffect(() => {
    // Initialize Auth: Check localStorage for token on app load
    const initializeAuth = () => {
      setIsLoading(true);
      try {
        const storedToken = localStorage.getItem('authToken');
        const storedUserString = localStorage.getItem('authUser');
        
        if (storedToken && storedUserString) {
          const storedUser: User = JSON.parse(storedUserString);
          setToken(storedToken);
          setUser(storedUser);
          setIsAuthenticated(true);
          authService.setAuthHeader(storedToken); // Set auth header for apiClient
          console.log('Auth initialized from localStorage');
        } else {
          console.log('No auth data in localStorage');
        }
      } catch (error) {
        console.error('Error initializing auth from localStorage:', error);
        // Clear potentially corrupted storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
      } finally {
        setIsLoading(false);
      }
    };
    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const response: AuthResponse = await authService.login(credentials);
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('authUser', JSON.stringify(response.user));
      setToken(response.access_token);
      setUser(response.user);
      setIsAuthenticated(true);
      authService.setAuthHeader(response.access_token);
      console.log('Login successful, token and user stored');
    } catch (error) {
      console.error('AuthContext login error:', error);
      throw error; // Re-throw to be caught by page component
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userInfo: RegisterUserInfo) => {
    setIsLoading(true);
    try {
      // Assuming register returns User, not AuthResponse (no immediate login)
      await authService.register(userInfo); 
      console.log('Registration successful (user info only, no token)');
      // Typically, after registration, user needs to verify email, then login.
      // So, we don't set isAuthenticated or token here.
    } catch (error) {
      console.error('AuthContext register error:', error);
      throw error; // Re-throw
    } finally {
      setIsLoading(false);
    }
  };

  const logoutContext = () => {
    setIsLoading(true);
    authService.logout(); // Call service logout (currently a placeholder)
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    authService.setAuthHeader(null); // Clear auth header for apiClient
    console.log('Logged out, token and user cleared');
    setIsLoading(false);
    // Typically, you'd also navigate to '/login' here using useNavigate,
    // but AuthContext shouldn't directly depend on react-router-dom's hooks.
    // Navigation should be handled by the component calling logoutContext or in App.tsx.
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, token, isLoading, login, register, logoutContext }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
