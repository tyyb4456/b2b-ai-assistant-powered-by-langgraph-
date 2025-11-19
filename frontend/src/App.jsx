import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/ErrorBoundary';

// Pages (we'll create these in next steps)
import Dashboard from './pages/Dashboard';
import NewConversation from './pages/NewConversation';
import ConversationDetail from './pages/ConversationDetail';
import History from './pages/History';
import Negotiations from './pages/Negotiations';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewConversation />} />
              <Route path="/conversation/:threadId" element={<ConversationDetail />} />
              <Route path="/history" element={<History />} />
              <Route path="/negotiations" element={<Negotiations />} />
            </Routes>
          </Layout>
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#fff',
                color: '#111827',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;