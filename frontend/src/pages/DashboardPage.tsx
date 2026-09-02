import React, { useEffect, useState } from 'react';
import { StatsSummary } from '../components/StatsSummary';
import { AlertTable } from '../components/AlertTable';
import {
  fetchDashboardStats,
  fetchAlerts,
  DashboardStats,
  AlertData,
} from '../services/api';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsRes, alertsRes] = await Promise.all([
          fetchDashboardStats(),
          fetchAlerts(1, 10),
        ]);
        setStats(statsRes);
        setAlerts(alertsRes.alerts);
      } catch (err) {
        console.error('Failed to load dashboard telemetry data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-400">
        Loading monitoring dashboard...
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Network Traffic Overview & Risk Dashboard
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Real-time Bitcoin node traffic analysis and anomaly detection metrics.
        </p>
      </div>

      <StatsSummary stats={stats} />

      <AlertTable alerts={alerts} />
    </div>
  );
};
