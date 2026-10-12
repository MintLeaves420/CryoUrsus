import React from 'react';
import type { Reading, Sensor } from '../types/domain';

interface ReadingsTableProps {
  readings: Reading[];
  sensors: Sensor[];
  lowerLimitC: number;
  upperLimitC: number;
}

export const ReadingsTable: React.FC<ReadingsTableProps> = ({
  readings,
  sensors,
  lowerLimitC,
  upperLimitC,
}) => {
  const sensorMap = new Map(sensors.map((s) => [s.id, s.label]));

  if (!readings || readings.length === 0) {
    return (
      <div style={{
        padding: '2rem',
        textAlign: 'center',
        color: '#64748b',
        fontSize: '0.875rem',
      }}>
        No readings logged yet. Start the simulation to stream telemetry.
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto', maxHeight: '340px', overflowY: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
        <thead>
          <tr style={{
            position: 'sticky',
            top: 0,
            background: 'var(--bg-secondary)',
            borderBottom: '1px solid var(--border-medium)',
            color: 'var(--text-muted)',
            textAlign: 'left',
          }}>
            <th style={{ padding: '0.6rem 0.8rem' }}>Timestamp</th>
            <th style={{ padding: '0.6rem 0.8rem' }}>Sensor Probe</th>
            <th style={{ padding: '0.6rem 0.8rem' }}>Temperature</th>
            <th style={{ padding: '0.6rem 0.8rem' }}>Data Quality</th>
            <th style={{ padding: '0.6rem 0.8rem' }}>Source</th>
          </tr>
        </thead>
        <tbody>
          {readings.slice(0, 30).map((r) => {
            const timeStr = new Date(r.timestamp).toLocaleTimeString();
            const sensorLabel = sensorMap.get(r.sensor_id) || r.sensor_id;
            const temp = r.temperature_c;

            let tempColor = '#f8fafc';
            let tempBadge = null;
            if (temp !== null && temp !== undefined) {
              if (temp > upperLimitC) {
                tempColor = 'var(--accent-rose)';
                tempBadge = '▲ High Breach';
              } else if (temp < lowerLimitC) {
                tempColor = 'var(--accent-sky)';
                tempBadge = '▼ Low Breach';
              } else {
                tempColor = 'var(--accent-emerald)';
              }
            }

            return (
              <tr
                key={r.id}
                style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  transition: 'background 0.1s ease',
                }}
              >
                <td style={{ padding: '0.55rem 0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  {timeStr}
                </td>
                <td style={{ padding: '0.55rem 0.8rem', fontWeight: 600 }}>
                  {sensorLabel}
                </td>
                <td style={{ padding: '0.55rem 0.8rem', fontFamily: 'var(--font-mono)', color: tempColor, fontWeight: 700 }}>
                  {temp !== null && temp !== undefined ? `${temp.toFixed(2)} °C` : '—'}
                  {tempBadge && (
                    <span style={{
                      marginLeft: '6px',
                      fontSize: '0.7rem',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      background: temp && temp > upperLimitC ? 'rgba(244, 63, 94, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                    }}>
                      {tempBadge}
                    </span>
                  )}
                </td>
                <td style={{ padding: '0.55rem 0.8rem' }}>
                  <span className={`badge ${
                    r.quality_status === 'valid'
                      ? 'badge-emerald'
                      : r.quality_status === 'stuck' || r.quality_status === 'disconnected'
                      ? 'badge-amber'
                      : 'badge-rose'
                  }`}>
                    {r.quality_status}
                  </span>
                </td>
                <td style={{ padding: '0.55rem 0.8rem', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                  {r.source}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
