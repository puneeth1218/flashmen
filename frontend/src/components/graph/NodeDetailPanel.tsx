import { useEffect, useState } from 'react';
import { fetchAlerts, AlertData } from '../../services/api';

interface Props {
  nodeId: string;
  label: string;
  entityType: string;
  riskScore: number;
  onClose: () => void;
}

export default function NodeDetailPanel({
  nodeId,
  label,
  entityType,
  riskScore,
  onClose,
}: Props) {
  const [alert, setAlert] = useState<AlertData | null>(null);
  const [loadingReason, setLoadingReason] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingReason(true);
    setAlert(null);

    fetchAlerts(1, 100)
      .then((res) => {
        if (cancelled) return;
        const match = res.alerts.find((a) => a.entity_id === nodeId);
        setAlert(match ?? null);
      })
      .catch((err) => {
        console.error('Failed to fetch alert detail:', err);
      })
      .finally(() => {
        if (!cancelled) setLoadingReason(false);
      });

    return () => {
      cancelled = true;
    };
  }, [nodeId]);

  return (
    <div className="node-detail-panel">
      <button className="close-btn" onClick={onClose} aria-label="Close">
        ×
      </button>
      <h3>{label}</h3>
      <p className="entity-id">
        {entityType} · {nodeId}
      </p>
      <div className="risk-score">
        Risk score: <strong>{riskScore}</strong>
      </div>

      {loadingReason ? (
        <div className="reason">Loading explanation…</div>
      ) : alert ? (
        <>
          <div className="reason">{alert.reason}</div>
          {Object.keys(alert.shap_explanation ?? {}).length > 0 && (
            <ul className="shap-list">
              {Object.entries(alert.shap_explanation)
                .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                .slice(0, 3)
                .map(([feature, contribution]) => (
                  <li key={feature}>
                    {feature}: {contribution > 0 ? '+' : ''}
                    {contribution.toFixed(1)}
                  </li>
                ))}
            </ul>
          )}
        </>
      ) : (
        <div className="reason">No alert record found for this entity.</div>
      )}
    </div>
  );
}