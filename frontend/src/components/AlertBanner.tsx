import React from 'react';
import type { Alert } from '../types/domain';
import { api } from '../services/api';

interface AlertBannerProps {
  alerts: Alert[];
  onAlertAcknowledged?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alerts, onAlertAcknowledged }) => {
  const activeAlerts = alerts.filter((a) => a.status === 'active');

  if (activeAlerts.length === 0) return null;

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.acknowledgeAlert(alertId, 'Operator Demo');
      onAlertAcknowledged?.();
    } catch (e) {
      console.error('Failed to acknowledge alert', e);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
      {activeAlerts.map((alert) => {
        const isCritical = alert.severity === 'critical';
        const isFault = alert.type === 'sensor_fault';

        let borderColor = isCritical ? 'var(--accent-rose)' : 'var(--accent-amber)';
        let bgColor = isCritical ? 'rgba(244, 63, 94, 0.12)' : 'rgba(245, 158, 11, 0.12)';
        let icon = isFault ? '⚠️' : isCritical ? '🚨' : '⚡';

        return (
          <div
            key={alert.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              background: bgColor,
              border: `1px solid ${borderColor}`,
              boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
              gap: '1rem',
              animation: 'pulse-subtle 2s infinite ease-in-out',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.25rem' }}>{icon}</span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#fff' }}>
                    {alert.title}
                  </span>
                  <span className={`badge ${isCritical ? 'badge-rose' : 'badge-amber'}`}>
                    {alert.severity}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {alert.message}
                </div>
              </div>
            </div>

            <button
              onClick={() => handleAcknowledge(alert.id)}
              className="btn btn-secondary"
              style={{ fontSize: '0.775rem', padding: '0.35rem 0.75rem' }}
            >
              Acknowledge
            </button>
          </div>
        );
      })}
    </div>
  );
};
