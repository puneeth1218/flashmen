import React from 'react';
import { AlertTable } from '../components/AlertTable';
import { FileUpload } from '../components/FileUpload';
import { useAlerts } from '../hooks/useAlerts';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { Activity } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { data: alerts, isLoading, isError } = useAlerts();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-zinc-800 flex flex-col">
      {/* Minimalist Top Navigation */}
      <header className="border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-sm sticky top-0 z-10 shrink-0">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-zinc-400" />
            <span className="font-semibold tracking-tight text-sm">Forensic Dashboard</span>
          </div>
          <Badge variant="success">System Online</Badge>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-6">
        <section>
          <FileUpload />
        </section>

        <section>
          {isLoading ? (
            <Card>
              <CardHeader>
                <CardTitle>
                  <Skeleton className="h-5 w-48" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              </CardContent>
            </Card>
          ) : isError ? (
            <Card>
              <CardContent className="p-8 text-center text-red-400 flex flex-col items-center gap-2">
                <span className="font-semibold">Unable to fetch alerts</span>
                <span className="text-sm text-red-400/80">Please ensure the backend API is reachable.</span>
              </CardContent>
            </Card>
          ) : (
            <AlertTable alerts={alerts || []} />
          )}
        </section>
      </main>
    </div>
  );
};
