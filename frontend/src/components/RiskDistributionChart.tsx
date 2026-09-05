import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';

interface RiskDistributionChartProps {
  distribution: Record<string, number>;
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({ distribution }) => {
  const buckets = Object.entries(distribution);
  const maxValue = Math.max(...buckets.map(([_, v]) => v), 1); // Avoid division by zero

  // Map buckets to colors matching our brutalist-lite semantic scale
  const getColor = (label: string) => {
    if (label.includes('76-100')) return 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]';
    if (label.includes('51-75')) return 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.4)]';
    if (label.includes('26-50')) return 'bg-sky-400 shadow-[0_0_10px_rgba(56,189,248,0.4)]';
    return 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]';
  };

  return (
    <Card className="w-full bg-zinc-950/80 border border-zinc-800/80 backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-zinc-800/80">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-mono text-zinc-400 uppercase tracking-widest font-semibold flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            Anomaly Risk Score Distribution
          </CardTitle>
          <span className="text-[11px] font-mono text-zinc-500">ML Calibrated Buckets</span>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="space-y-4">
          {buckets.map(([label, value]) => {
            const percentage = Math.round((value / maxValue) * 100);
            return (
              <div key={label} className="space-y-1.5 group">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-zinc-300">Score Range: {label}</span>
                  <span className="text-zinc-400 font-semibold group-hover:text-cyan-400 transition-colors">
                    {value.toLocaleString()} <span className="text-zinc-600 font-normal">entities</span>
                  </span>
                </div>
                <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden border border-zinc-800/60">
                  <div 
                    className={`h-full ${getColor(label)} transition-all duration-1000 ease-out`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
