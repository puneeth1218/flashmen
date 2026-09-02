import React from 'react';
import { DashboardStats } from '../services/api';
import { AlertOctagon, Activity, Users, Radio } from 'lucide-react';

interface StatsSummaryProps {
  stats: DashboardStats | null;
}

export const StatsSummary: React.FC<StatsSummaryProps> = ({ stats }) => {
  if (!stats) {
    return <div className="text-gray-400 text-sm">Loading summary metrics...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Total Transactions</p>
            <p className="text-2xl font-bold text-white mt-1">
              {stats.total_transactions_ingested.toLocaleString()}
            </p>
          </div>
          <Activity className="h-8 w-8 text-blue-400" />
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">High Risk Alerts</p>
            <p className="text-2xl font-bold text-red-500 mt-1">
              {stats.high_risk_alerts_count}
            </p>
          </div>
          <AlertOctagon className="h-8 w-8 text-red-500" />
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Monitored Entities</p>
            <p className="text-2xl font-bold text-white mt-1">
              {stats.total_entities_monitored.toLocaleString()}
            </p>
          </div>
          <Users className="h-8 w-8 text-amber-400" />
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Active P2P Peers</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {stats.active_peers_count}
            </p>
          </div>
          <Radio className="h-8 w-8 text-emerald-400" />
        </div>
      </div>
    </div>
  );
};
