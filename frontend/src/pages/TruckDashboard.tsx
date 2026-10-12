import React, { useState } from 'react';
import type { Shipment, Reading, Alert, ShipmentSummary } from '../types/domain';
import { Package3D } from '../components/Package3D';
import { SimulationControls } from '../components/SimulationControls';
import { TemperatureChart } from '../components/TemperatureChart';
import { ReadingsTable } from '../components/ReadingsTable';
import { AlertBanner } from '../components/AlertBanner';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { NFCTransferModal } from '../components/NFCTransferModal';

interface TruckDashboardProps {
  shipment: Shipment;
  readings: Reading[];
  alerts: Alert[];
  summary: ShipmentSummary | null;
  onShipmentUpdated: (updated: Shipment) => void;
  onAlertsChanged: () => void;
}

export const TruckDashboard: React.FC<TruckDashboardProps> = ({
  shipment,
  readings,
  alerts,
  summary,
  onShipmentUpdated,
  onAlertsChanged,
}) => {
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null);
  const [isNFCModalOpen, setIsNFCModalOpen] = useState(false);

  const profile = shipment.profile;
  const lowerLimit = profile?.lower_limit_c ?? 2.0;
  const upperLimit = profile?.upper_limit_c ?? 8.0;

  const selectedSensor = shipment.sensors.find((s) => s.id === selectedSensorId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Active Alerts Banner */}
      <AlertBanner alerts={alerts} onAlertAcknowledged={onAlertsChanged} />

      {/* Main Interactive Row: 3D Package View + Controls */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(340px, 1.3fr) minmax(320px, 1fr)',
        gap: '1.25rem',
      }}>
        {/* 3D Package Visualizer Panel */}
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>🧊</span>
                <span>3D Insulated Package & Thermal Cavity</span>
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                3×3 Vial Array ({shipment.vial_count} / 9 Active) • {shipment.sensor_count} Independent Telemetry Probes
              </span>
            </div>
            <span className="badge badge-cyan">
              {profile?.category || 'Cold-Chain Shipper'}
            </span>
          </div>

          {/* 3D Canvas Container */}
          <div style={{ height: '380px', width: '100%', position: 'relative' }}>
            <Package3D
              vialCount={shipment.vial_count}
              sensors={shipment.sensors}
              selectedSensorId={selectedSensorId}
              onSelectSensor={(id) => setSelectedSensorId(id === selectedSensorId ? null : id)}
              lowerLimitC={lowerLimit}
              upperLimitC={upperLimit}
            />
          </div>

          {/* Selected Sensor Quick Telemetry Strip */}
          {selectedSensor && (
            <div style={{
              background: 'rgba(10, 19, 34, 0.8)',
              border: '1px solid var(--border-accent)',
              borderRadius: 'var(--radius-md)',
              padding: '0.65rem 0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.8rem',
            }}>
              <div>
                <span style={{ fontWeight: 700, color: '#fff' }}>{selectedSensor.label}</span>
                <span style={{ marginLeft: '8px', color: 'var(--text-dim)' }}>({selectedSensor.id})</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className={`badge ${selectedSensor.health_status === 'healthy' ? 'badge-emerald' : 'badge-amber'}`}>
                  {selectedSensor.health_status}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                  {selectedSensor.last_valid_temperature_c !== null && selectedSensor.last_valid_temperature_c !== undefined
                    ? `${selectedSensor.last_valid_temperature_c.toFixed(2)} °C`
                    : 'N/A'}
                </span>
                <button
                  onClick={() => setSelectedSensorId(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '11px' }}
                >
                  ✕ Clear
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Simulator Lifecycle & Scenario Control Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <SimulationControls
            shipment={shipment}
            onShipmentUpdated={onShipmentUpdated}
            onOpenNFCModal={() => setIsNFCModalOpen(true)}
          />

          {/* Explainable Decision Support Preview */}
          <ExplanationPanel summary={summary} />
        </div>
      </div>

      {/* Second Row: Real-time Curves + Readings Log Table */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(340px, 1.4fr) minmax(320px, 1fr)',
        gap: '1.25rem',
      }}>
        {/* Real-Time Temperature Chart */}
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>📈</span>
                <span>Live Thermal Telemetry History</span>
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Target Storage Envelope: {lowerLimit.toFixed(1)}°C to {upperLimit.toFixed(1)}°C
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Latest 40 Time Cycles
            </span>
          </div>

          <TemperatureChart
            readings={readings}
            sensors={shipment.sensors}
            lowerLimitC={lowerLimit}
            upperLimitC={upperLimit}
            selectedSensorId={selectedSensorId}
          />
        </div>

        {/* Real-Time Readings Log Table */}
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>📋</span>
                <span>Timestamped Sensor Logs</span>
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Authoritative SQLite Audit Records ({readings.length} total observations)
              </span>
            </div>
          </div>

          <ReadingsTable
            readings={readings}
            sensors={shipment.sensors}
            lowerLimitC={lowerLimit}
            upperLimitC={upperLimit}
          />
        </div>
      </div>

      {/* NFC Modal */}
      <NFCTransferModal
        shipmentId={shipment.id}
        isOpen={isNFCModalOpen}
        onClose={() => setIsNFCModalOpen(false)}
      />
    </div>
  );
};
