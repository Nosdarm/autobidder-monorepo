import React, { Suspense } from 'react' // Import Suspense
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css' // or globals.css
import { QueryClientProvider } from '@tanstack/react-query'
import queryClient from './lib/react-query'
import './i18n'; // Import i18n configuration

// Placeholder for a loading spinner or simple text
const loadingMarkup = (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    Loading translations...
  </div>
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Suspense fallback={loadingMarkup}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </Suspense>
  </React.StrictMode>,
)
