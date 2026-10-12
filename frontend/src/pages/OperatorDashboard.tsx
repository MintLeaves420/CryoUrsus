import React, { useState } from 'react';
import type { Shipment, Reading, Alert, ShipmentSummary, Assessment } from '../types/domain';
import { api } from '../services/api';
import { TemperatureChart } from '../components/TemperatureChart';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { AlertBanner } from '../components/AlertBanner';

interface OperatorDashboardProps {
  shipment: Shipment;
  readings: Reading[];
  alerts: Alert[];
  summary: ShipmentSummary | null;
  assessment: Assessment | null;
  onShipmentUpdated: (updated: Shipment) => void;
  onAlertsChanged: () => void;
  onAssessmentUpdated: (updated: Assessment) => void;
}

export const OperatorDashboard: React.FC<OperatorDashboardProps> = ({
  shipment,
  readings,
  alerts,
  summary,
  assessment,
  onShipmentUpdated,
  onAlertsChanged,
  onAssessmentUpdated,
}) => {
  const [reviewStatus, setReviewStatus] = useState<string>(
    assessment?.review_status || shipment.operator_review_status || 'reviewed'
  );
  const [reviewNote, setReviewNote] = useState<string>(
    assessment?.review_note || shipment.operator_review_note || ''
  );
  const [reviewerName, setReviewerName] = useState<string>(
    assessment?.reviewer_label || 'Lead QA Operator (Demo User)'
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitFeedback, setSubmitFeedback] = useState<string | null>(null);

  const profile = shipment.profile;
  const lowerLimit = profile?.lower_limit_c ?? 2.0;
  const upperLimit = profile?.upper_limit_c ?? 8.0;

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitFeedback(null);
    try {
      const updated = await api.submitAssessment(shipment.id, {
        review_status: reviewStatus,
        review_note: reviewNote,
        reviewer_label: reviewerName,
      });
      onAssessmentUpdated(updated);
      setSubmitFeedback('✓ Human assessment disposition persisted to database.');
      // Refresh shipment record to reflect operator review fields
      const refreshedShipment = await api.getShipment(shipment.id);
      onShipmentUpdated(refreshedShipment);
    } catch (err: any) {
      alert(err.message || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Alert Banner */}
      <AlertBanner alerts={alerts} onAlertAcknowledged={onAlertsChanged} />

      {/* Top Overview Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem',
      }}>
        {/* Technical Status Card */}
        <div className="metric-card">
          <span className="metric-label">Computed Technical Status</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span className={`badge ${
              shipment.active_alerts_count > 0 ? 'badge-rose' : 'badge-emerald'
            }`} style={{ fontSize: '0.85rem' }}>
              {shipment.active_alerts_count > 0 ? 'Excursion Alert Active' : 'Normal / In Envelope'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Authoritative backend telemetry logic
          </span>
        </div>

        {/* Human Review Status Card */}
        <div className="metric-card">
          <span className="metric-label">Human Review Disposition</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span className={`badge ${
              (shipment.operator_review_status || assessment?.review_status) === 'reviewed'
                ? 'badge-emerald'
                : 'badge-amber'
            }`} style={{ fontSize: '0.85rem' }}>
              {(shipment.operator_review_status || assessment?.review_status || 'PENDING REVIEW').toUpperCase()}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Explicitly distinct from technical status
          </span>
        </div>

        {/* Telemetry Reliability Card */}
        <div className="metric-card">
          <span className="metric-label">Data Quality & Telemetry</span>
          <span className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
            {summary ? `${(summary.valid_data_coverage * 100).toFixed(1)}%` : '—'}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {summary?.data_quality_status || 'Analyzing telemetry...'}
          </span>
        </div>

        {/* Total Excursion Duration Card */}
        <div className="metric-card">
          <span className="metric-label">Cumulative Breach Duration</span>
          <span className="metric-value" style={{ color: summary && summary.excursion_duration_seconds > 0 ? 'var(--accent-amber)' : 'inherit' }}>
            {summary ? `${summary.excursion_duration_seconds.toFixed(0)} s` : '0 s'}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {summary?.crossing_count || 0} event transitions recorded
          </span>
        </div>
      </div>

      {/* Main Grid: Chart & Decision Explanation */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(350px, 1.4fr) minmax(320px, 1fr)',
        gap: '1.25rem',
      }}>
        {/* Temperature History Chart */}
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>📈</span>
                <span>Audit Telemetry Curve</span>
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Configured: {lowerLimit}°C to {upperLimit}°C • Destination: {shipment.destination_label}
              </span>
            </div>
            <a
              href={api.getReportPdfUrl(shipment.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', textDecoration: 'none', color: '#fff', padding: '0.35rem 0.75rem' }}
            >
              📄 Download PDF
            </a>
          </div>

          <TemperatureChart
            readings={readings}
            sensors={shipment.sensors}
            lowerLimitC={lowerLimit}
            upperLimitC={upperLimit}
          />
        </div>

        {/* Explainable Decision Support Panel */}
        <ExplanationPanel summary={summary} />
      </div>

      {/* Operator Human Assessment & Disposition Form */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>✍️</span>
            <span>Operator Review & Chain-of-Custody Disposition</span>
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Record human assessment notes and disposition for regulatory/quality inspection
          </span>
        </div>

        {submitFeedback && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--accent-emerald)',
            color: '#a7f3d0',
            padding: '0.6rem 0.8rem',
            borderRadius: '6px',
            fontSize: '0.825rem',
            marginBottom: '1rem',
          }}>
            {submitFeedback}
          </div>
        )}

        <form onSubmit={handleSubmitReview} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Review Status Disposition:</label>
              <select
                value={reviewStatus}
                onChange={(e) => setReviewStatus(e.target.value)}
                className="form-select"
                required
              >
                <option value="reviewed">✅ Reviewed & Acceptable for Transport</option>
                <option value="requires_follow_up">⚠️ Requires Follow-up / Quarantine Inspection</option>
                <option value="pending">⏳ Pending Further Technical Assessment</option>
              </select>
            </div>

            <div>
              <label className="form-label">Reviewer Identification / Role:</label>
              <input
                type="text"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                className="form-input"
                required
              />
            </div>
          </div>

          <div>
            <label className="form-label">Operator Review Notes & Thermal Excursion Rationale:</label>
            <textarea
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              className="form-textarea"
              rows={3}
              placeholder="Record observations, packaging seal integrity, dry ice / eutectic plate levels, or quarantine disposition..."
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              Note: Human assessment actions are committed immutably to the SQLite audit log.
            </span>
            <button type="submit" disabled={isSubmitting} className="btn btn-primary">
              {isSubmitting ? 'Saving Assessment...' : 'Commit Review Disposition'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
