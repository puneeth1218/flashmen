import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTable } from '../components/AlertTable';
import { FileUpload } from '../components/FileUpload';
import { StatsSummary } from '../components/StatsSummary';
import { useAlerts } from '../hooks/useAlerts';
import { fetchDashboardStats, DashboardStats } from '../services/api/alerts';
import { Skeleton } from '../components/ui/Skeleton';
import { ShieldAlert, Radio, Cpu } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { data: alerts, isLoading: alertsLoading, isError: alertsError } = useAlerts();

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 6000,
  });

  return (
    <div className="min-h-screen flex flex-col bg-[#07090e] text-slate-100 selection:bg-cyan-500 selection:text-black">
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 space-y-10 relative z-10">
        
        {/* Executive Command Header */}
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-zinc-800/80">
            <div className="flex items-center gap-2 text-xs font-mono tracking-wider text-zinc-400">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span>NETWORK SURVEILLANCE DESK</span>
              <span className="text-zinc-600">/</span>
              <span className="text-zinc-300">THREAT INTELLIGENCE</span>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/80 border border-zinc-800">
                <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
                <span className="text-zinc-300">MAINNET TELEMETRY: SYNCED</span>
              </div>
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/80 border border-zinc-800">
                <Cpu className="w-3 h-3 text-cyan-400" />
                <span className="text-zinc-300">ISOLATION ENGINE: ACTIVE</span>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <h1 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Bitcoin Network Surveillance <br className="hidden sm:inline" />
              <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
                &amp; Threat Command Center
              </span>
            </h1>
            <p className="mt-3 text-sm md:text-base text-zinc-400 max-w-3xl leading-relaxed">
              Real-time anomaly scoring, graph peel-chain heuristics, and SHAP explainability matrices for high-risk wallets and Sybil network actors.
            </p>
          </div>
        </section>

        {/* Top Metric KPI Row */}
        <section>
          <StatsSummary stats={stats ?? null} />
        </section>

        {/* Telemetry Ingestion Zone */}
        <section>
          <FileUpload />
        </section>

        {/* Alerts & Anomalies Section */}
        <section id="alerts-section" className="pt-4">
          {alertsLoading ? (
            <div className="p-8 rounded-3xl bg-zinc-950 border border-zinc-800/80 space-y-4">
              <div className="flex items-center justify-between mb-6">
                <Skeleton className="h-7 w-64 bg-zinc-900" />
                <Skeleton className="h-5 w-24 bg-zinc-900" />
              </div>
              <Skeleton className="h-14 w-full bg-zinc-900" />
              <Skeleton className="h-14 w-full bg-zinc-900" />
              <Skeleton className="h-14 w-full bg-zinc-900" />
              <Skeleton className="h-14 w-full bg-zinc-900" />
            </div>
          ) : alertsError ? (
            <div className="p-12 text-center rounded-3xl bg-zinc-950 border border-red-900/40 text-red-400 flex flex-col items-center justify-center gap-3">
              <ShieldAlert className="w-10 h-10 text-red-500" />
              <p className="font-semibold text-lg text-white">Threat Stream Disconnected</p>
              <p className="text-xs text-zinc-400 max-w-md">
                Unable to query alert endpoints. Ensure the FastAPI backend server is running and accessible on port 8000.
              </p>
            </div>
          ) : (
            <AlertTable alerts={alerts || []} />
          )}
        </section>
      </main>
    </div>
  );
};
