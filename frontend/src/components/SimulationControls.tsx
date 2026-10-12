import React, { useState } from 'react';
import type { Shipment } from '../types/domain';
import { api } from '../services/api';

interface SimulationControlsProps {
  shipment: Shipment;
  onShipmentUpdated: (updated: Shipment) => void;
  onOpenNFCModal: () => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  shipment,
  onShipmentUpdated,
  onOpenNFCModal,
}) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleStart = async () => {
    try {
      setLoadingAction('start');
      const updated = await api.startShipment(shipment.id);
      onShipmentUpdated(updated);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handlePause = async () => {
    try {
      setLoadingAction('pause');
      const updated = await api.pauseShipment(shipment.id);
      onShipmentUpdated(updated);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleResume = async () => {
    try {
      setLoadingAction('resume');
      const updated = await api.resumeShipment(shipment.id);
      onShipmentUpdated(updated);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleEnd = async () => {
    if (!confirm('Are you sure you want to end and finalize this simulation run?')) return;
    try {
      setLoadingAction('end');
      const updated = await api.endShipment(shipment.id);
      onShipmentUpdated(updated);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleScenarioChange = async (scenario: string) => {
    try {
      setLoadingAction('scenario');
      const updated = await api.setScenario(shipment.id, scenario);
      onShipmentUpdated(updated);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const isRunning = shipment.status === 'running';
  const isPaused = shipment.status === 'paused';
  const isCompleted = shipment.status === 'completed';

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Top Bar: Status and Main Lifecycle Buttons */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span className={`beacon-dot ${shipment.status}`} />
          <span style={{ fontWeight: 700, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            STATUS: {shipment.status}
          </span>
          <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
            ID: {shipment.id}
          </span>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {shipment.status === 'created' && (
            <button
              onClick={handleStart}
              disabled={loadingAction !== null}
              className="btn btn-primary"
            >
              ▶ Start Simulation
            </button>
          )}

          {isRunning && (
            <button
              onClick={handlePause}
              disabled={loadingAction !== null}
              className="btn btn-warning"
            >
              ⏸ Pause
            </button>
          )}

          {isPaused && (
            <button
              onClick={handleResume}
              disabled={loadingAction !== null}
              className="btn btn-primary"
            >
              ▶ Resume
            </button>
          )}

          {!isCompleted && (
            <button
              onClick={handleEnd}
              disabled={loadingAction !== null}
              className="btn btn-danger"
            >
              ⏹ Finalize & End
            </button>
          )}
        </div>
      </div>

      {/* Scenario Selection Bar (The Core Judge Interaction Bar) */}
      <div style={{
        background: 'rgba(10, 19, 34, 0.7)',
        padding: '0.85rem 1rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>🎛️</span>
          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Scenario Generator Mode:
            </span>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              Trigger physical anomalies or excursions during live presentation
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <select
            value={shipment.scenario}
            onChange={(e) => handleScenarioChange(e.target.value)}
            disabled={isCompleted || loadingAction !== null}
            className="form-select"
            style={{ minWidth: '220px', padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}
          >
            <option value="normal">✅ Normal (Steady In-Range)</option>
            <option value="gradual_warming">🔥 Gradual Warming (Upper Breach)</option>
            <option value="gradual_cooling">❄️ Gradual Cooling (Lower Breach)</option>
            <option value="sudden_spike">⚡ Sudden Heat Spike (+4.5°C)</option>
            <option value="sudden_drop">🧊 Sudden Cryo Drop (-4.5°C)</option>
            <option value="repeated_fluctuations">〰️ Repeated Oscillations</option>
            <option value="stuck">🔒 Sensor Stuck (Frozen Telemetry)</option>
            <option value="disconnected">🔌 Sensor Disconnected (Loss of Signal)</option>
            <option value="implausible">❌ Implausible Reading (Unphysical 148°C)</option>
          </select>
        </div>
      </div>

      {/* NFC & Report Download Action Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', paddingTop: '0.25rem' }}>
        <button
          onClick={onOpenNFCModal}
          className="btn btn-secondary"
          style={{ fontSize: '0.825rem' }}
        >
          📱 Simulated NFC Scan & Handoff
        </button>

        <a
          href={api.getReportPdfUrl(shipment.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ textDecoration: 'none', fontSize: '0.825rem', color: 'var(--text-main)' }}
        >
          📄 Download PDF Telemetry Report
        </a>
      </div>
    </div>
  );
};
