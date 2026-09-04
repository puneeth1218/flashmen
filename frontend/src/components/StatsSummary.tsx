import React from 'react';
import { DashboardStats } from '../services/api/alerts';
import { Activity, ShieldAlert, Coins, Network } from 'lucide-react';

interface StatsSummaryProps {
  stats: DashboardStats | null;
}

export const StatsSummary: React.FC<StatsSummaryProps> = ({ stats }) => {
  const totalTx = stats?.total_transactions_ingested ?? 0;
  const criticalThreats = stats?.critical_threat_entities ?? stats?.critical_alerts ?? 0;
  const anomalousVolume = stats?.anomalous_volume_btc ?? 0;
  const dominantPattern = stats?.dominant_pattern || (stats?.total_alerts ? "Multi-IP Broadcast" : "None (Idle)");

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* 1. Total Transactions Ingested */}
      <div className="relative overflow-hidden bg-gradient-to-b from-zinc-900/90 to-zinc-950/90 p-5 rounded-2xl border border-zinc-800/80 shadow-lg hover:border-cyan-500/40 transition-all group">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] font-mono uppercase tracking-wider text-zinc-400">
            Total Ingested
          </span>
          <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 shadow-cyber-glow group-hover:scale-105 transition-transform">
            <Activity className="w-4 h-4" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-2xl lg:text-3xl font-mono font-bold text-white tracking-tight">
            {totalTx.toLocaleString()} <span className="text-xs font-normal text-zinc-500">TXS</span>
          </div>
          <p className="text-[11px] text-zinc-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            Raw Bitcoin traffic records
          </p>
        </div>
      </div>

      {/* 2. Critical Threat Entities */}
      <div className="relative overflow-hidden bg-gradient-to-b from-zinc-900/90 to-zinc-950/90 p-5 rounded-2xl border border-zinc-800/80 shadow-lg hover:border-red-500/40 transition-all group">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] font-mono uppercase tracking-wider text-zinc-400">
            Critical Threats
          </span>
          <div className="w-8 h-8 rounded-lg bg-red-950/60 border border-red-800/40 flex items-center justify-center text-red-400 shadow-threat-glow group-hover:scale-105 transition-transform">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl lg:text-3xl font-mono font-bold text-red-400 tracking-tight">
              {criticalThreats}
            </span>
            {criticalThreats > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-950/80 text-red-400 border border-red-800/60 animate-pulse">
                RISK &gt; 90
              </span>
            )}
          </div>
          <p className="text-[11px] text-zinc-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
            High-confidence anomalies
          </p>
        </div>
      </div>

      {/* 3. Anomalous Volume (BTC) */}
      <div className="relative overflow-hidden bg-gradient-to-b from-zinc-900/90 to-zinc-950/90 p-5 rounded-2xl border border-zinc-800/80 shadow-lg hover:border-amber-500/40 transition-all group">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] font-mono uppercase tracking-wider text-zinc-400">
            Anomalous Volume
          </span>
          <div className="w-8 h-8 rounded-lg bg-amber-950/60 border border-amber-800/40 flex items-center justify-center text-amber-400 shadow-sm group-hover:scale-105 transition-transform">
            <Coins className="w-4 h-4" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-2xl lg:text-3xl font-mono font-bold text-amber-300 tracking-tight">
            {anomalousVolume.toLocaleString()} <span className="text-xs font-normal text-zinc-500">BTC</span>
          </div>
          <p className="text-[11px] text-zinc-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            Flagged in Peel/Mixer flows
          </p>
        </div>
      </div>

      {/* 4. Dominant Anomaly Pattern */}
      <div className="relative overflow-hidden bg-gradient-to-b from-zinc-900/90 to-zinc-950/90 p-5 rounded-2xl border border-zinc-800/80 shadow-lg hover:border-purple-500/40 transition-all group">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] font-mono uppercase tracking-wider text-zinc-400">
            Dominant Pattern
          </span>
          <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/40 flex items-center justify-center text-purple-400 shadow-sm group-hover:scale-105 transition-transform">
            <Network className="w-4 h-4" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-lg lg:text-xl font-bold text-zinc-100 truncate tracking-tight" title={dominantPattern}>
            {dominantPattern}
          </div>
          <p className="text-[11px] text-zinc-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
            Primary explainability cluster
          </p>
        </div>
      </div>
    </div>
  );
};
