import React, { Suspense, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Skeleton } from './components/ui/Skeleton';
import { clearAlerts } from './services/api/alerts';

const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const GraphPage = React.lazy(() => import('./pages/GraphPage').then(m => ({ default: m.GraphPage })));
const UploadPage = React.lazy(() => import('./pages/UploadPage').then(m => ({ default: m.UploadPage })));

const PageLoader = () => (
  <div className="p-8 space-y-4 max-w-7xl mx-auto">
    <Skeleton className="h-10 w-1/3" />
    <Skeleton className="h-64 w-full" />
    <Skeleton className="h-64 w-full" />
  </div>
);

export const App: React.FC = () => {
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    // Automatically clear previous logs on initial site load / reload
    clearAlerts()
      .catch((err) => {
        console.warn('Failed to clear previous logs on reload:', err);
      })
      .finally(() => {
        setCleared(true);
      });

    // Send beacon to clear logs when page unloads or reloads
    const handleBeforeUnload = () => {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        navigator.sendBeacon(`${baseUrl}/api/v1/alerts/clear`);
      } catch (e) {
        // ignore
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  if (!cleared) {
    return <PageLoader />;
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col font-sans bg-transparent text-ink selection:bg-electric-blue selection:text-black relative">
        <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/graph" element={<GraphPage />} />
              <Route path="/upload" element={<UploadPage />} />
            </Routes>
          </Suspense>
        </main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
