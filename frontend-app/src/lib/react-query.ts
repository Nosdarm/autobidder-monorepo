import { QueryClient } from '@tanstack/react-query';
// import { useToast } from '@/hooks/useToast'; // Could be used for non-401 errors

// const { showToastError } = useToast(); // Cannot use hooks at the top level

const handleGlobalError = (error: any) => {
  // In a real app, you might want to use a logger here
  console.error("Global React Query Error:", error);

  if (error?.response?.status === 401) {
    // TODO: Implement proper navigation, perhaps clear auth state via AuthContext.
    // For now, direct redirect. This will cause a full page reload.
    // Also, consider if AuthContext needs to be cleared *before* redirect.
    // Accessing AuthContext here directly is complex.
    // One strategy is to emit a custom event that App.tsx listens for to trigger logout.
    
    // Temporarily clear auth from localStorage, though AuthContext might still hold it in memory
    // until a reload or explicit logoutContext call.
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    
    window.location.href = '/login'; // Redirect to login
    // alert('Session expired or unauthorized. Please log in again.'); // Alternative to toast if hook is not available
  } else {
    // For other errors, you might show a generic toast, but often these are handled by useMutation/useQuery's onError.
    // Example:
    // const errorMessage = error?.response?.data?.message || 'An unexpected error occurred';
    // toast.error(errorMessage); // This would require toast to be available globally or useToast to be callable here
    // For simplicity, we'll rely on specific error handling in components or individual query/mutation options.
    console.error("Unhandled React Query Error (Non-401):", error?.response?.data?.message || error.message);
  }
};

const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      onError: handleGlobalError,
    },
    queries: {
      onError: handleGlobalError,
      // Configure retries for queries, but not for 401s usually
      retry: (failureCount, error: any) => {
        if (error?.response?.status === 401) {
          return false; // Do not retry on 401
        }
        // Default retry behavior (e.g., 3 times)
        return failureCount < 3;
      },
    },
  },
});

export default queryClient;
