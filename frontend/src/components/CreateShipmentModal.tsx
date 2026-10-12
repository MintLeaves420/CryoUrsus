import React, { useState } from 'react';
import type { ProductProfile, Shipment } from '../types/domain';
import { api } from '../services/api';

interface CreateShipmentModalProps {
  profiles: ProductProfile[];
  isOpen: boolean;
  onClose: () => void;
  onShipmentCreated: (shipment: Shipment) => void;
}

export const CreateShipmentModal: React.FC<CreateShipmentModalProps> = ({
  profiles,
  isOpen,
  onClose,
  onShipmentCreated,
}) => {
  const [profileId, setProfileId] = useState<string>(profiles[0]?.id || '');
  const [vialCount, setVialCount] = useState<number>(9);
  const [sensorCount, setSensorCount] = useState<number>(4);
  const [scenario, setScenario] = useState<string>('normal');
  const [destination, setDestination] = useState<string>('Judge Demo Bio-Depot (Chicago Hub)');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const selectedProfile = profiles.find((p) => p.id === profileId) || profiles[0];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const created = await api.createShipment({
        profile_id: profileId || selectedProfile.id,
        vial_count: Number(vialCount),
        sensor_count: Number(sensorCount),
        scenario,
        destination_label: destination,
      });
      onShipmentCreated(created);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to initialize shipment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.4rem' }}>📦</span>
            <div>
              <h3 style={{ fontSize: '1.1rem' }}>Configure Simulated Shipment</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Select illustrative thermal profile and package container configuration
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              fontSize: '1.2rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          {error && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid var(--accent-rose)',
              color: '#fecdd3',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.8rem',
            }}>
              {error}
            </div>
          )}

          {/* Product Profile Dropdown */}
          <div>
            <label className="form-label">Product Profile (Illustrative Benchmark):</label>
            <select
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
              className="form-select"
              required
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.lower_limit_c}°C to {p.upper_limit_c}°C)
                </option>
              ))}
            </select>
            {selectedProfile && (
              <div style={{
                marginTop: '0.35rem',
                fontSize: '0.75rem',
                color: 'var(--accent-cyan)',
                background: 'rgba(6, 182, 212, 0.08)',
                padding: '0.4rem 0.6rem',
                borderRadius: '4px',
              }}>
                Target Envelope: <b>{selectedProfile.lower_limit_c}°C</b> to <b>{selectedProfile.upper_limit_c}°C</b> • <i>{selectedProfile.notes}</i>
              </div>
            )}
          </div>

          {/* Vial Count and Sensor Count in 2 columns */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Vial Count in 3×3 Tray (1 to 9):</label>
              <input
                type="number"
                min={1}
                max={9}
                value={vialCount}
                onChange={(e) => setVialCount(Math.min(9, Math.max(1, parseInt(e.target.value) || 1)))}
                className="form-input"
                required
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px', display: 'block' }}>
                Remaining slots rendered vacant
              </span>
            </div>

            <div>
              <label className="form-label">Sensor Telemetry Probes (1 to 10):</label>
              <input
                type="number"
                min={1}
                max={10}
                value={sensorCount}
                onChange={(e) => setSensorCount(Math.min(10, Math.max(1, parseInt(e.target.value) || 1)))}
                className="form-input"
                required
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px', display: 'block' }}>
                Core center, lid, base, flanks
              </span>
            </div>
          </div>

          {/* Initial Scenario */}
          <div>
            <label className="form-label">Initial Simulation Scenario:</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="form-select"
            >
              <option value="normal">Normal (Stable within limits)</option>
              <option value="gradual_warming">Gradual Warming (Upper breach progression)</option>
              <option value="gradual_cooling">Gradual Cooling (Lower breach progression)</option>
              <option value="sudden_spike">Sudden Spike (Rapid heat pulse)</option>
              <option value="sudden_drop">Sudden Drop (Rapid deep freeze)</option>
              <option value="repeated_fluctuations">Repeated Oscillations (Transitions demo)</option>
              <option value="stuck">Sensor Stuck (Frozen sensor detection)</option>
              <option value="disconnected">Sensor Disconnected (Signal loss)</option>
              <option value="implausible">Implausible Reading (148°C anomaly)</option>
            </select>
          </div>

          {/* Destination */}
          <div>
            <label className="form-label">Simulated Destination / Route:</label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="form-input"
              placeholder="e.g. Judge Demo Testing Center"
            />
          </div>

          {/* Footer Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Creating...' : 'Initialize Shipment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
