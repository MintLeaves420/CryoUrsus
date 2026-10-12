import React from 'react';
import type { ShipmentSummary } from '../types/domain';

interface ExplanationPanelProps {
  summary?: ShipmentSummary | null;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ summary }) => {
  if (!summary) {
    return (
      <div className="glass-panel" style={{ padding: '1.25rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
        Loading decision model data...
      </div>
    );
  }

  const score = summary.demo_score;
  const isInsufficient = score === null || score === undefined;

  let gaugeColor = 'var(--accent-emerald)';
  if (isInsufficient) {
    gaugeColor = 'var(--text-dim)';
  } else if (score < 70) {
    gaugeColor = 'var(--accent-rose)';
  } else if (score < 90) {
    gaugeColor = 'var(--accent-amber)';
  }

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>🧬</span>
            <span>Illustrative Viability Model</span>
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Transparent Deterministic Decision Support • Method: {summary.method_version}
          </span>
        </div>
        <span className="badge badge-purple">
          {isInsufficient ? 'NO CONFIDENCE' : 'DEMO ESTIMATE'}
        </span>
      </div>

      {/* Main Score Display */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '1.5rem',
        padding: '1rem',
        background: 'rgba(10, 19, 34, 0.6)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
      }}>
        {/* Radial / Box Score */}
        <div style={{
          minWidth: '85px',
          height: '85px',
          borderRadius: '50%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: `3px solid ${gaugeColor}`,
          boxShadow: `0 0 16px ${gaugeColor}40`,
          background: 'rgba(5, 11, 20, 0.8)',
        }}>
          <span style={{
            fontFamily: 'var(--font-display)',
            fontSize: isInsufficient ? '1.1rem' : '1.75rem',
            fontWeight: 800,
            color: gaugeColor,
          }}>
            {isInsufficient ? 'N/A' : score.toFixed(1)}
          </span>
          {!isInsufficient && <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>/ 100</span>}
        </div>

        {/* Status description */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
            {summary.demo_label || 'Awaiting telemetry...'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Telemetry Reliability: <b style={{ color: 'var(--accent-cyan)' }}>{(summary.valid_data_coverage * 100).toFixed(1)}%</b> valid data coverage ({summary.valid_readings_count} / {summary.total_readings} ticks).
          </div>
        </div>
      </div>

      {/* Extracted Features Grid */}
      <div>
        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', marginBottom: '0.5rem', fontWeight: 600 }}>
          Deterministic Input Features:
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '0.5rem',
          fontSize: '0.8rem',
        }}>
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.7rem' }}>BREACH COUNT</span>
            <span style={{ fontWeight: 700, color: summary.crossing_count > 0 ? 'var(--accent-amber)' : 'var(--text-main)' }}>
              {summary.crossing_count} Events
            </span>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.7rem' }}>EXCURSION TIME</span>
            <span style={{ fontWeight: 700 }}>
              {summary.excursion_duration_seconds.toFixed(0)} Seconds
            </span>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.7rem' }}>PEAK EXTREME</span>
            <span style={{ fontWeight: 700, color: summary.peak_temperature_c ? 'var(--accent-rose)' : 'inherit' }}>
              {summary.peak_temperature_c !== null && summary.peak_temperature_c !== undefined ? `${summary.peak_temperature_c.toFixed(1)}°C` : '—'}
            </span>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.7rem' }}>MIN EXTREME</span>
            <span style={{ fontWeight: 700, color: summary.minimum_temperature_c ? 'var(--accent-sky)' : 'inherit' }}>
              {summary.minimum_temperature_c !== null && summary.minimum_temperature_c !== undefined ? `${summary.minimum_temperature_c.toFixed(1)}°C` : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Decision Factors & Plain Language Reasoning */}
      <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
          Decision Path & Rules:
        </div>
        <ul style={{ listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.8rem', color: 'var(--text-main)' }}>
          {summary.explanation.map((item, idx) => (
            <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
              <span style={{ color: 'var(--accent-cyan)' }}>•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Mandatory Safety & Non-Validation Disclaimer */}
      <div style={{
        fontSize: '0.75rem',
        color: '#fde68a',
        background: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.25)',
        borderRadius: '6px',
        padding: '0.5rem 0.75rem',
        lineHeight: 1.4,
      }}>
        ⚠️ <b>Safety Notice:</b> {summary.disclaimer} This calculation informs human evaluation; it does not grant release permission for real pharmaceutical product.
      </div>
    </div>
  );
};
