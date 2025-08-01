import axios from 'axios';

// 1. API Base URL
// Use environment variable, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create an Axios instance for API calls
// This instance can be used by other services as well.
// If we create a dedicated api.ts for this, authService would import it.
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. Interface Definitions
export interface LoginCredentials {
  email: string; // In backend, it's 'username' which is email
  password: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  is_active?: boolean;
  is_verified?: boolean;
  role?: string; // e.g., 'user', 'admin', 'superadmin'
  // Add other user fields as necessary
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User; // Include user details in the auth response
}

export interface RegisterUserInfo {
  name: string;
  email: string;
  password: string;
}

// 3. AuthService Functions
export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      // Backend /auth/login expects 'email'
      const response = await apiClient.post<AuthResponse>('/auth/login', {
        email: credentials.email, // Changed from username
        password: credentials.password,
      });
      return response.data;
    } catch (error: any) {
      // Axios errors have a 'response' property
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      throw new Error(errorMessage);
    }
  },

  register: async (userInfo: RegisterUserInfo): Promise<User> => {
    try {
      // Assuming the backend /users/ endpoint is for registration
      // Adjust if there's a specific /auth/register endpoint
        const { name, ...payload } = userInfo; // Destructure to exclude name from payload
        const response = await apiClient.post<User>('/auth/register', payload); 
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed';
      throw new Error(errorMessage);
    }
  },

  sendPasswordResetEmail: async (email: string): Promise<void> => {
    try {
      // Conceptual endpoint, adjust if backend has this
      await apiClient.post('/auth/forgot-password', { email }); 
      console.log('Password reset email request sent for:', email);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to send password reset email.';
      throw new Error(errorMessage);
    }
  },

  // verifyEmail: async (token: string): Promise<void> => { // Conceptual
  //   try {
  //     await apiClient.post('/auth/verify-email', { token });
  //   } catch (error: any) {
  //     throw new Error(error.response?.data?.detail || 'Email verification failed.');
  //   }
  // },

  logout: (): void => {
    // In a real app, this might call a backend /auth/logout endpoint
    // to invalidate the token on the server-side if using a blacklist.
    // For now, it's primarily a client-side state clearing operation handled by AuthContext.
    console.log('Logout requested (client-side). Token clearing handled by AuthContext.');
  },

  // Helper to update Authorization header on the apiClient instance
  setAuthHeader: (token: string | null) => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },

  // Expose the apiClient if other parts of the app need to make authenticated requests
  // with the same base configuration and interceptors (if added later to apiClient).
  // Alternatively, a dedicated api.ts file can export the configured client.
  getClient: () => apiClient,
};

// --- Axios Interceptor for Global Error Handling ---
// This interceptor is added to the apiClient instance created above.
apiClient.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    if (error.response) {
      const { status } = error.response;
      if (status === 401 || status === 403) {
        // Unauthorized or Forbidden
        console.error(`AuthService Interceptor: Received ${status} error. Logging out.`);
        
        // Perform actions similar to logoutContext, but without React context dependency
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        authService.setAuthHeader(null); // Clear auth header on the apiClient

        // Redirect to login page
        // Avoid using useNavigate here as this is not a React component.
        // A robust way is to dispatch a custom event that App.tsx listens to,
        // or simply reload to a path that will force redirection if not authenticated.
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'; 
          // Note: This is a hard redirect. A more SPA-friendly way might involve
          // an event bus or checking a global "session expired" flag in routing.
        }
      }
    }
    // It's important to return a rejected promise to allow calling code's .catch() to handle it
    return Promise.reject(error);
  }
);


// Example of how to set the token when app initializes or after login
// This is typically handled by AuthContext after login.
// const token = localStorage.getItem('authToken');
// authService.setAuthHeader(token);

export default authService;
