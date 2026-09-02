import React, { useState } from 'react';
import { AlertData } from '../services/api';
import { AlertTriangle, ChevronRight, Info } from 'lucide-react';

interface AlertTableProps {
  alerts: AlertData[];
  onSelectAlert?: (alert: AlertData) => void;
}

export const AlertTable: React.FC<AlertTableProps> = ({ alerts, onSelectAlert }) => {
  const [selectedEntity, setSelectedEntity] = useState<AlertData | null>(null);

  const getRiskBadgeColor = (score: number) => {
    if (score >= 75) return 'bg-red-900/50 text-red-400 border-red-700';
    if (score >= 40) return 'bg-amber-900/50 text-amber-400 border-amber-700';
    return 'bg-emerald-900/50 text-emerald-400 border-emerald-700';
  };

  const handleRowClick = (alert: AlertData) => {
    setSelectedEntity(alert);
    if (onSelectAlert) {
      onSelectAlert(alert);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-5 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          Anomalous Traffic & Transaction Alerts
        </h3>
        <span className="text-xs bg-gray-700 text-gray-300 px-3 py-1 rounded-full">
          {alerts.length} Detected
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-900/50 text-xs uppercase text-gray-400 font-semibold border-b border-gray-700">
            <tr>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Entity Identifier</th>
              <th className="px-6 py-4">Risk Score</th>
              <th className="px-6 py-4">Confidence</th>
              <th className="px-6 py-4">Primary Reason</th>
              <th className="px-6 py-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {alerts.map((alert, idx) => (
              <tr
                key={`${alert.entity_id}-${idx}`}
                onClick={() => handleRowClick(alert)}
                className="hover:bg-gray-700/40 cursor-pointer transition"
              >
                <td className="px-6 py-4">
                  <span
                    className={`inline-block px-2.5 py-1 text-xs font-semibold rounded uppercase ${
                      alert.entity_type === 'wallet'
                        ? 'bg-purple-900/40 text-purple-400 border border-purple-800'
                        : 'bg-blue-900/40 text-blue-400 border border-blue-800'
                    }`}
                  >
                    {alert.entity_type}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-gray-200">{alert.entity_id}</td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRiskBadgeColor(
                      alert.risk_score
                    )}`}
                  >
                    {alert.risk_score.toFixed(1)} / 100
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-gray-400">
                  {(alert.confidence * 100).toFixed(0)}%
                </td>
                <td className="px-6 py-4 max-w-md truncate text-gray-300">{alert.reason}</td>
                <td className="px-6 py-4 text-right">
                  <ChevronRight className="h-5 w-5 text-gray-400 inline" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SHAP Explanation Modal Stub */}
      {selectedEntity && (
        <div className="p-6 bg-gray-900/80 border-t border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-white flex items-center gap-2">
              <Info className="h-4 w-4 text-amber-400" />
              SHAP Feature Attribution: {selectedEntity.entity_id}
            </h4>
            <button
              onClick={() => setSelectedEntity(null)}
              className="text-gray-400 hover:text-white text-xs"
            >
              Close Breakdown
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            {Object.entries(selectedEntity.shap_explanation).map(([feat, val]) => (
              <div key={feat} className="bg-gray-800 p-3 rounded border border-gray-700">
                <span className="text-gray-400 block">{feat}</span>
                <span className="text-amber-400 font-bold text-sm">
                  +{(val * 100).toFixed(1)}% risk impact
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
