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
    if (label.includes('76-100')) return 'bg-red-500';
    if (label.includes('51-75')) return 'bg-yellow-500';
    if (label.includes('26-50')) return 'bg-fog';
    return 'bg-green-500';
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-4 border-b border-canvas">
        <CardTitle className="text-[11px] font-mono text-fog uppercase tracking-widest font-semibold">Risk Distribution</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-4">
          {buckets.map(([label, value]) => {
            const percentage = Math.round((value / maxValue) * 100);
            return (
              <div key={label} className="space-y-1 group">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-zinc-300">Score {label}</span>
                  <span className="text-zinc-500 group-hover:text-zinc-300 transition-colors">{value.toLocaleString()}</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
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
