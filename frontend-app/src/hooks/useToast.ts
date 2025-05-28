import toast, { ToastOptions } from 'react-hot-toast';

interface CustomToastOptions extends ToastOptions {
  // You can add custom options here if needed later
}

export function useToast() {
  const showToastSuccess = (message: string, options?: CustomToastOptions) => {
    toast.success(message, options);
  };

  const showToastError = (message: string, options?: CustomToastOptions) => {
    toast.error(message, options);
  };

  const showToastInfo = (message: string, options?: CustomToastOptions) => {
    // react-hot-toast doesn't have a default 'info' icon like some libraries.
    // You can use a custom icon or just `toast()` for neutral messages.
    // For simplicity, we'll use toast() which is neutral.
    toast(message, { ...options, icon: options?.icon || 'ℹ️' }); // Or a custom SVG/Lucide icon
  };

  const showToastLoading = (message: string, options?: CustomToastOptions) => {
    return toast.loading(message, options);
  };

  const dismissToast = (toastId?: string) => {
    toast.dismiss(toastId);
  };

  return {
    showToastSuccess,
    showToastError,
    showToastInfo,
    showToastLoading,
    dismissToast,
    // You can also export `toast` directly if needed for specific cases like promise toasts
    // rawToast: toast, 
  };
}
