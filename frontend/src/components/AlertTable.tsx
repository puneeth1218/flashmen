import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AlertData, clearAlerts } from '../services/api/alerts';
import { ShieldAlert, Trash2 } from 'lucide-react';
import { Badge, BadgeVariant } from './ui/Badge';
import { Sheet } from './ui/Sheet';

interface AlertTableProps {
  alerts: AlertData[];
  onSelectAlert?: (alert: AlertData) => void;
}

export const AlertTable: React.FC<AlertTableProps> = ({ alerts, onSelectAlert }) => {
  const [selectedEntity, setSelectedEntity] = useState<AlertData | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const queryClient = useQueryClient();

  const getRiskBadgeVariant = (score: number): BadgeVariant => {
    if (score >= 75) return 'critical';
    if (score >= 40) return 'warning';
    return 'neutral';
  };

  const cleanReason = (reason?: string): string => {
    return (reason || '').replace(/^flagged due to:\s*/i, '').trim();
  };

  const uniqueAlerts = React.useMemo(() => {
    const seen = new Set<string>();
    const result: AlertData[] = [];
    for (const alert of alerts) {
      const key = `${alert.entity_id}-${alert.entity_type}`;
      if (!seen.has(key)) {
        seen.add(key);
        result.push({
          ...alert,
          reason: cleanReason(alert.reason),
        });
      }
    }
    return result;
  }, [alerts]);

  const handleRowClick = (alert: AlertData) => {
    setSelectedEntity(alert);
    if (onSelectAlert) {
      onSelectAlert(alert);
    }
  };

  const handleClearAll = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsClearing(true);
    try {
      await clearAlerts();
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    } catch (err) {
      console.error('Failed to clear alerts:', err);
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <>
      <div className="bg-paper rounded-apple-card shadow-none overflow-hidden pb-4 border border-hairline relative z-10">
        <div className="p-8 flex items-center justify-between">
          <h3 className="text-[32px] font-semibold text-ink tracking-apple-subhead">
            Selected Alerts
          </h3>
          <div className="flex items-center gap-4">
            <span className="text-[17px] tracking-apple-body text-mid-gray">
              {uniqueAlerts.length} Detected
            </span>
            {uniqueAlerts.length > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                disabled={isClearing}
                className="text-[13px] px-3.5 py-1.5 rounded-full border border-hairline hover:border-red-500/50 hover:bg-red-500/10 text-mid-gray hover:text-red-400 transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                {isClearing ? 'Clearing...' : 'Clear All Logs'}
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto px-4">
          <table className="w-full text-left text-[17px] text-ink tracking-apple-body">
            <thead className="bg-transparent text-[14px] font-medium text-mid-gray border-b border-hairline/50">
              <tr>
                <th className="px-4 py-4 font-normal">Type</th>
                <th className="px-4 py-4 font-normal">Entity Identifier</th>
                <th className="px-4 py-4 font-normal">Risk Score</th>
                <th className="px-4 py-4 font-normal">Confidence</th>
                <th className="px-4 py-4 font-normal">Primary Reason</th>
                <th className="px-4 py-4 text-right font-normal">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline/30">
              {uniqueAlerts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-mid-gray tracking-apple-body">
                    No alerts found
                  </td>
                </tr>
              ) : (
                uniqueAlerts.map((alert, idx) => (
                  <tr
                    key={`${alert.entity_id}-${idx}`}
                    onClick={() => handleRowClick(alert)}
                    className="hover:bg-canvas cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-5">
                      <span className="text-[14px] tracking-apple-body text-mid-gray">
                        {alert.entity_type}
                      </span>
                    </td>
                    <td className="px-4 py-5 font-mono text-ink text-[14px]">{alert.entity_id}</td>
                    <td className="px-4 py-5">
                      <Badge variant={getRiskBadgeVariant(alert.risk_score)}>
                        {alert.risk_score.toFixed(1)} / 100
                      </Badge>
                    </td>
                    <td className="px-4 py-5 text-mid-gray text-[14px]">
                      {(alert.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-5 max-w-md truncate text-mid-gray text-[14px]">{alert.reason}</td>
                    <td className="px-4 py-5 text-right">
                      <span className="text-[24px] text-link-blue hover:opacity-70 leading-none transition-opacity">›</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Sheet 
        isOpen={!!selectedEntity} 
        onClose={() => setSelectedEntity(null)}
        title="Alert Details"
      >
        {selectedEntity && (
          <div className="space-y-6 text-sm">
            {/* Header / Identity */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded uppercase bg-zinc-800 text-zinc-300 border border-zinc-700">
                  {selectedEntity.entity_type}
                </span>
                <Badge variant={getRiskBadgeVariant(selectedEntity.risk_score)}>
                  Risk Score: {selectedEntity.risk_score.toFixed(1)}
                </Badge>
              </div>
              <h3 className="text-xl font-mono text-zinc-50 break-all border-b border-zinc-800 pb-4">
                {selectedEntity.entity_id}
              </h3>
            </div>

            {/* Reason */}
            <div>
              <h4 className="font-semibold text-zinc-400 uppercase text-xs mb-2 tracking-wider">Detection Reason</h4>
              <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-md text-zinc-300 leading-relaxed">
                {selectedEntity.reason}
              </div>
            </div>

            {/* SHAP Values */}
            {selectedEntity.shap_explanation && Object.keys(selectedEntity.shap_explanation).length > 0 && (
              <div>
                <h4 className="font-semibold text-zinc-400 uppercase text-xs mb-2 tracking-wider flex items-center gap-2">
                  <ShieldAlert className="h-3 w-3" />
                  SHAP Feature Attribution
                </h4>
                <div className="bg-zinc-900 border border-zinc-800 rounded-md divide-y divide-zinc-800 font-mono text-xs">
                  {Object.entries(selectedEntity.shap_explanation).map(([feature, impact]) => {
                    const impactPercentage = (impact * 100).toFixed(1);
                    const isPositive = impact >= 0;
                    return (
                      <div key={feature} className="flex items-center justify-between p-3 hover:bg-zinc-800/50 transition-colors">
                        <span className="text-zinc-400">{feature}</span>
                        <span className={isPositive ? 'text-amber-400' : 'text-emerald-400'}>
                          {isPositive ? '+' : ''}{impactPercentage}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </Sheet>
    </>
  );
};
