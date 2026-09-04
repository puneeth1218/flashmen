import React from 'react';
import { AlertTable } from '../components/AlertTable';
import { FileUpload } from '../components/FileUpload';
import { useAlerts } from '../hooks/useAlerts';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
// import removed
import { Skeleton } from '../components/ui/Skeleton';
// import removed

export const DashboardPage: React.FC = () => {
  const { data: alerts, isLoading, isError } = useAlerts();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Main Content Area */}
      <main className="flex-1 w-full relative z-10">
        {/* Hero Section */}
        <section className="w-full bg-transparent pt-24 pb-32">
          <div className="max-w-[1200px] mx-auto px-8">
            <h1 className="text-[80px] font-bold tracking-apple-hero text-white leading-[1.04] mb-16 max-w-4xl">
              Forensic analysis. <br/>
              <span className="text-mid-gray">Clearer than ever.</span>
            </h1>
            <FileUpload />
          </div>
        </section>

        {/* Alerts Section */}
        <section className="w-full bg-transparent py-32 border-t border-hairline/30">
          <div className="max-w-[1200px] mx-auto px-8">
            <h2 className="text-[40px] font-bold tracking-apple-heading text-ink mb-12">
              Detected Anomalies
            </h2>
            {isLoading ? (
              <Card>
                <CardHeader>
                  <CardTitle>
                    <Skeleton className="h-5 w-48" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </div>
                </CardContent>
              </Card>
            ) : isError ? (
              <Card>
                <CardContent className="p-12 text-center text-ember flex flex-col items-center gap-3">
                  <span className="font-semibold text-lg">Unable to fetch alerts</span>
                  <span className="text-mid-gray">Please ensure the backend API is reachable.</span>
                </CardContent>
              </Card>
            ) : (
              <AlertTable alerts={alerts || []} />
            )}
          </div>
        </section>
      </main>
    </div>
  );
};
