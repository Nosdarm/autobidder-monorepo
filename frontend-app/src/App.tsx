import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from 'next-themes'; // Import ThemeProvider
import { AuthProvider, useAuth } from './components/contexts/AuthContext';
import { Toaster } from 'react-hot-toast'; // Import Toaster

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import { Loader2 } from 'lucide-react'; // Import Loader2
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';

// Other Pages (Placeholders)
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import ProfilesPage from './pages/ProfilesPage'; // Added import
import BidHistoryPage from './pages/BidHistoryPage'; // Import BidHistoryPage
import BidDetailPage from './pages/BidDetailPage'; // Import BidDetailPage
import MLAnalyticsPage from './pages/MLAnalyticsPage'; // Import MLAnalyticsPage

// Import the main layout component
import MainLayout from './components/layout/MainLayout'; // Updated import

// Conceptual AuthLayout (can remain here or be moved)
const AuthLayout: React.FC = () => {
  // Layout specific to auth pages, e.g. centered content
  return (
    <div>
      <Outlet />
    </div>
  );
};


// ProtectedRoute Component
interface ProtectedRouteProps {
  // children?: ReactNode; // Using Outlet for nested routes is preferred for element prop
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />; // Renders child routes if authenticated
};


function AppRoutes() {
  const { isLoading } = useAuth(); // Access isLoading to prevent premature rendering

  // This specific "Loading application..." might be redundant if ProtectedRoute already handles it,
  // but if there are routes accessible *before* ProtectedRoute kicks in (e.g. public routes that
  // still wait for auth resolution for some reason), this can be a global loader.
  // For now, we'll apply the same spinner. If distinct behavior is needed, it can be adjusted.
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes with AuthLayout */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Route>

      {/* Public Routes without MainLayout (or using a different simple layout if needed) */}
      {/* For this example, HomePage will not use MainLayout to show distinction.
          If HomePage should also use MainLayout, it can be nested similarly to dashboard. */}
      <Route path="/" element={<HomePage />} /> 
      {/* Add other public pages like About, Contact etc. here, potentially under a simple public layout */}
      
      {/* Protected Routes are wrapped by ProtectedRoute and then MainLayout */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}> {/* MainLayout now wraps all protected routes */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profiles" element={<ProfilesPage />} /> {/* New Route Added */}
          <Route path="/bids" element={<BidHistoryPage />} /> {/* Add /bids route */}
          <Route path="/bids/:id" element={<BidDetailPage />} /> {/* Add /bids/:id route */}
          <Route path="/ml/metrics" element={<MLAnalyticsPage />} /> {/* Add /ml/metrics route */}
          {/* Example: <Route path="/prompts" element={<AIPromptsPage />} /> */}
        </Route>
      </Route>

      {/* Fallback for unmatched routes */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <AuthProvider> {/* AuthProvider wraps everything that needs auth context */}
          <Toaster position="top-center" reverseOrder={false} /> {/* Add Toaster here */}
          {/* AppRoutes now contains the actual route definitions */}
          <AppRoutes /> 
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
