import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { AlertData, clearAlerts } from '../services/api/alerts';
import { 
  ShieldAlert, 
  Trash2, 
  Copy, 
  Check, 
  ChevronRight, 
  Wallet, 
  Network, 
  AlertTriangle,
  Layers,
  Activity,
  GitFork
} from 'lucide-react';
import { Sheet } from './ui/Sheet';

interface AlertTableProps {
  alerts: AlertData[];
  onSelectAlert?: (alert: AlertData) => void;
}

type FilterTab = 'all' | 'wallet' | 'ip' | 'critical';

export const AlertTable: React.FC<AlertTableProps> = ({ alerts, onSelectAlert }) => {
  const navigate = useNavigate();
  const [selectedEntity, setSelectedEntity] = useState<AlertData | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const queryClient = useQueryClient();

  const cleanReason = (reason?: string): string => {
    return (reason || '').replace(/^flagged due to:\s*/i, '').trim();
  };

  // Deduplicate alerts across entities
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

  // Apply Quick Filter Tabs
  const filteredAlerts = React.useMemo(() => {
    switch (activeTab) {
      case 'wallet':
        return uniqueAlerts.filter(a => a.entity_type === 'wallet');
      case 'ip':
        return uniqueAlerts.filter(a => a.entity_type === 'ip');
      case 'critical':
        return uniqueAlerts.filter(a => a.risk_score >= 90);
      case 'all':
      default:
        return uniqueAlerts;
    }
  }, [uniqueAlerts, activeTab]);

  const counts = React.useMemo(() => {
    return {
      all: uniqueAlerts.length,
      wallet: uniqueAlerts.filter(a => a.entity_type === 'wallet').length,
      ip: uniqueAlerts.filter(a => a.entity_type === 'ip').length,
      critical: uniqueAlerts.filter(a => a.risk_score >= 90).length,
    };
  }, [uniqueAlerts]);

  const handleRowClick = (alert: AlertData) => {
    setSelectedEntity(alert);
    if (onSelectAlert) {
      onSelectAlert(alert);
    }
  };

  const handleCopy = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(id).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const handleClearAll = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsClearing(true);
    try {
      await clearAlerts();
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setShowClearConfirm(false);
    } catch (err) {
      console.error('Failed to clear alerts:', err);
    } finally {
      setIsClearing(false);
    }
  };

  const formatEntityId = (id: string) => {
    if (id.length > 20) {
      return `${id.slice(0, 8)}...${id.slice(-8)}`;
    }
    return id;
  };

  const getRiskBadgeStyles = (score: number) => {
    if (score >= 85) {
      return {
        bg: 'bg-red-950/80',
        text: 'text-red-400',
        border: 'border-red-800/80',
        glow: 'shadow-threat-glow',
        label: 'CRITICAL',
      };
    }
    if (score >= 50) {
      return {
        bg: 'bg-amber-950/80',
        text: 'text-amber-400',
        border: 'border-amber-800/80',
        glow: 'shadow-sm',
        label: 'SUSPICIOUS',
      };
    }
    return {
      bg: 'bg-cyan-950/80',
      text: 'text-cyan-400',
      border: 'border-cyan-800/80',
      glow: 'shadow-cyber-glow',
      label: 'ELEVATED',
    };
  };

  // Parse dynamic feature weights from reason string for explainability bars
  const extractExplainabilityFeatures = (reason: string, fallbackShap?: Record<string, number>) => {
    const featureRegex = /([A-Za-z0-9\s\-()]+?)\s*\(([0-9.]+)%\)/g;
    const parsed: Array<{ name: string; weight: number }> = [];
    let match;
    while ((match = featureRegex.exec(reason)) !== null) {
      parsed.push({
        name: match[1].trim(),
        weight: parseFloat(match[2]),
      });
    }

    if (parsed.length > 0) {
      return parsed;
    }

    if (fallbackShap && Object.keys(fallbackShap).length > 0) {
      return Object.entries(fallbackShap).map(([k, v]) => ({
        name: k.replace(/_/g, ' ').toUpperCase(),
        weight: Math.round(Math.abs(v) * 100),
      }));
    }

    return [{ name: 'Anomalous Network Correlation', weight: 85 }];
  };

  return (
    <>
      <div id="alerts-section" className="w-full bg-zinc-950 rounded-3xl border border-zinc-800/80 shadow-2xl overflow-hidden backdrop-blur-md">
        {/* Table Header & Controls */}
        <div className="p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-zinc-800/80">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
              <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight font-mono">
                Threat Detection Center
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-zinc-900 border border-zinc-800 text-zinc-300">
                {uniqueAlerts.length} Entities Flagged
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Active anomaly signals identified across graph topology, transaction flows, and IP broadcast vectors.
            </p>
          </div>

          {/* Action Tools */}
          <div className="flex items-center gap-3">
            {uniqueAlerts.length > 0 && (
              <>
                {showClearConfirm ? (
                  <div className="flex items-center gap-2 bg-zinc-900 p-1 rounded-xl border border-red-800/60">
                    <span className="text-[11px] text-zinc-300 px-2">Clear all records?</span>
                    <button
                      type="button"
                      onClick={handleClearAll}
                      disabled={isClearing}
                      className="px-2.5 py-1 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold transition-colors cursor-pointer"
                    >
                      {isClearing ? 'Clearing...' : 'Confirm'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowClearConfirm(false)}
                      className="px-2 py-1 rounded-lg bg-zinc-800 text-zinc-300 hover:text-white text-xs transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowClearConfirm(true)}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-zinc-800 hover:border-red-500/50 bg-zinc-900/80 hover:bg-red-950/20 text-zinc-400 hover:text-red-400 text-xs font-medium transition-all cursor-pointer shadow-sm"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Clear All Logs
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Quick Filter Tabs */}
        <div className="px-6 md:px-8 py-3 bg-zinc-900/40 border-b border-zinc-800/60 flex items-center gap-2 overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'all'
                ? 'bg-zinc-800 text-white border border-zinc-700 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
            }`}
          >
            All Entities ({counts.all})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('wallet')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'wallet'
                ? 'bg-purple-950/80 text-purple-300 border border-purple-800/80 shadow-sm'
                : 'text-zinc-400 hover:text-purple-300 hover:bg-zinc-800/40'
            }`}
          >
            <Wallet className="w-3 h-3 text-purple-400" />
            Wallets Only ({counts.wallet})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('ip')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'ip'
                ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/80 shadow-sm'
                : 'text-zinc-400 hover:text-cyan-300 hover:bg-zinc-800/40'
            }`}
          >
            <Network className="w-3 h-3 text-cyan-400" />
            IPs Only ({counts.ip})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('critical')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'critical'
                ? 'bg-red-950/80 text-red-300 border border-red-800/80 shadow-sm'
                : 'text-zinc-400 hover:text-red-300 hover:bg-zinc-800/40'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-red-400" />
            Critical (&gt;90) ({counts.critical})
          </button>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="bg-zinc-950/80 text-[11px] font-mono uppercase tracking-wider text-zinc-400 border-b border-zinc-800/80">
              <tr>
                <th className="px-6 py-4 font-semibold">Entity Type</th>
                <th className="px-6 py-4 font-semibold">Identifier Address</th>
                <th className="px-6 py-4 font-semibold">Risk Score</th>
                <th className="px-6 py-4 font-semibold">Confidence</th>
                <th className="px-6 py-4 font-semibold">Primary Detection Reason</th>
                <th className="px-6 py-4 text-right font-semibold">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center text-zinc-500">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <ShieldAlert className="w-8 h-8 text-zinc-600" />
                      <p className="text-sm font-medium text-zinc-400">No anomalous entities detected</p>
                      <p className="text-xs text-zinc-500">
                        {uniqueAlerts.length === 0 
                          ? 'Upload a Bitcoin telemetry file above to trigger anomaly detection.' 
                          : 'No entities match the active filter criteria.'}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert, idx) => {
                  const riskStyle = getRiskBadgeStyles(alert.risk_score);
                  const isCopied = copiedId === alert.entity_id;

                  return (
                    <tr
                      key={`${alert.entity_id}-${idx}`}
                      onClick={() => handleRowClick(alert)}
                      className="hover:bg-zinc-900/60 cursor-pointer transition-colors group"
                    >
                      {/* Entity Type Badge */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        {alert.entity_type === 'wallet' ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-purple-950/60 text-purple-300 border border-purple-800/60 shadow-sm">
                            <Wallet className="w-3 h-3 text-purple-400" />
                            WALLET
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 shadow-sm">
                            <Network className="w-3 h-3 text-cyan-400" />
                            IP NODE
                          </span>
                        )}
                      </td>

                      {/* Entity Identifier with Copy Button */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span 
                            className="font-mono text-zinc-200 text-[13px] font-medium group-hover:text-cyan-400 transition-colors"
                            title={alert.entity_id}
                          >
                            {formatEntityId(alert.entity_id)}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => handleCopy(alert.entity_id, e)}
                            className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer"
                            title="Copy full identifier"
                          >
                            {isCopied ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </td>

                      {/* Risk Score */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${riskStyle.bg} ${riskStyle.text} ${riskStyle.border} ${riskStyle.glow}`}>
                            {alert.risk_score.toFixed(1)} / 100
                          </span>
                        </div>
                      </td>

                      {/* Confidence */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div 
                              className="h-full bg-cyan-400 rounded-full" 
                              style={{ width: `${Math.min(alert.confidence * 100, 100)}%` }}
                            />
                          </div>
                          <span className="font-mono text-xs text-zinc-400">
                            {(alert.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>

                      {/* Primary Reason */}
                      <td className="px-6 py-4 max-w-md">
                        <p className="text-xs text-zinc-300 font-medium leading-relaxed truncate" title={alert.reason}>
                          {alert.reason}
                        </p>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/graph?entity_id=${encodeURIComponent(alert.entity_id)}`);
                            }}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-amber-950/50 text-amber-400 hover:text-amber-300 hover:bg-amber-900/60 border border-amber-800/50 transition-all cursor-pointer shadow-sm"
                            title="Explore entity neighborhood in topology graph"
                          >
                            <GitFork className="w-3.5 h-3.5" />
                            Explore Graph
                          </button>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); handleRowClick(alert); }}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 group-hover:translate-x-0.5 transition-all cursor-pointer px-1.5 py-1"
                          >
                            Inspect
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Forensic Entity Detail Inspection Drawer */}
      <Sheet 
        isOpen={!!selectedEntity} 
        onClose={() => setSelectedEntity(null)}
        title="Forensic Threat Inspection"
      >
        {selectedEntity && (
          <div className="space-y-6">
            {/* Header & Identity Card */}
            <div className="p-4 rounded-2xl bg-zinc-900/80 border border-zinc-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-bold uppercase border ${
                  selectedEntity.entity_type === 'wallet'
                    ? 'bg-purple-950/60 text-purple-300 border-purple-800/60'
                    : 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                }`}>
                  {selectedEntity.entity_type === 'wallet' ? <Wallet className="w-3 h-3" /> : <Network className="w-3 h-3" />}
                  {selectedEntity.entity_type}
                </span>

                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${getRiskBadgeStyles(selectedEntity.risk_score).bg} ${getRiskBadgeStyles(selectedEntity.risk_score).text} ${getRiskBadgeStyles(selectedEntity.risk_score).border}`}>
                    Risk: {selectedEntity.risk_score.toFixed(1)} / 100
                  </span>
                </div>
              </div>

              {/* Full Address with Copy */}
              <div className="space-y-1">
                <label className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">
                  Full Entity Address / Hash
                </label>
                <div className="p-2.5 rounded-xl bg-zinc-950 border border-zinc-800/90 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-white break-all select-all">
                    {selectedEntity.entity_id}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => handleCopy(selectedEntity.entity_id, e)}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer shrink-0"
                    title="Copy full address"
                  >
                    {copiedId === selectedEntity.entity_id ? (
                      <Check className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Anomaly Detection Reason */}
            <div className="p-4 rounded-2xl bg-zinc-900/80 border border-zinc-800 space-y-2">
              <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                Detection Explanation
              </h4>
              <p className="text-xs text-zinc-200 leading-relaxed bg-zinc-950 p-3 rounded-xl border border-zinc-800/90 font-medium">
                {selectedEntity.reason}
              </p>
            </div>

            {/* Dynamic Feature Explainability Breakdown */}
            <div className="p-4 rounded-2xl bg-zinc-900/80 border border-zinc-800 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
                  SHAP Risk Attribution Breakdown
                </h4>
                <span className="text-[10px] font-mono text-zinc-500">Confidence: {(selectedEntity.confidence * 100).toFixed(0)}%</span>
              </div>

              <div className="space-y-3">
                {extractExplainabilityFeatures(selectedEntity.reason, selectedEntity.shap_explanation).map((item, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-zinc-300 font-medium">{item.name}</span>
                      <span className="font-mono font-bold text-cyan-400">{item.weight}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-zinc-950 overflow-hidden border border-zinc-800">
                      <div 
                        className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 rounded-full"
                        style={{ width: `${Math.min(item.weight, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Investigative Metadata */}
            <div className="p-4 rounded-2xl bg-zinc-900/80 border border-zinc-800 space-y-3 text-xs">
              <h4 className="font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                Forensic Graph Signals
              </h4>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800/80">
                  <span className="text-zinc-500 block">Anomaly Heuristic</span>
                  <span className="text-white font-medium">Isolation Forest v2</span>
                </div>
                <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800/80">
                  <span className="text-zinc-500 block">Vector Classification</span>
                  <span className="text-emerald-400 font-medium">Peel/Mixer Topology</span>
                </div>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="pt-2 flex items-center gap-3">
              <button
                type="button"
                onClick={() => {
                  navigate(`/graph?entity_id=${encodeURIComponent(selectedEntity.entity_id)}`);
                }}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black text-xs font-mono font-bold flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer"
              >
                <GitFork className="w-4 h-4" />
                Explore Graph
              </button>
              <button
                type="button"
                onClick={() => setSelectedEntity(null)}
                className="w-full py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Close Inspection
              </button>
            </div>
          </div>
        )}
      </Sheet>
    </>
  );
};
