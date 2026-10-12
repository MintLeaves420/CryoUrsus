import React from 'react';

interface HeaderProps {
  activeTab: 'truck' | 'operator' | 'owner';
  onTabChange: (tab: 'truck' | 'operator' | 'owner') => void;
  isWsConnected: boolean;
  onOpenCreateModal: () => void;
  currentShipmentId?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  isWsConnected,
  onOpenCreateModal,
  currentShipmentId,
}) => {
  return (
    <>
      <header className="app-header">
        {/* Brand Logo & Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #06b6d4, #2563eb)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.4)',
          }}>
            🐻‍❄️
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.25rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(135deg, #fff, #94a3b8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                CryoUrsus
              </span>
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                {currentShipmentId ? `SHIPMENT: ${currentShipmentId}` : 'HACKATHON SIMULATOR'}
              </span>
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)' }}>
              Explainable Cold-Chain Telemetry & Decision-Support
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="nav-tab-group">
          <button
            onClick={() => onTabChange('truck')}
            className={`nav-tab ${activeTab === 'truck' ? 'active' : ''}`}
          >
            🚚 Truck / Package
          </button>
          <button
            onClick={() => onTabChange('operator')}
            className={`nav-tab ${activeTab === 'operator' ? 'active' : ''}`}
          >
            🔬 Operator Review
          </button>
          <button
            onClick={() => onTabChange('owner')}
            className={`nav-tab ${activeTab === 'owner' ? 'active' : ''}`}
          >
            📊 Owner & Fleet
          </button>
        </div>

        {/* Action Controls & WebSocket Telemetry Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          {/* Connection status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.75rem',
            fontWeight: 600,
            padding: '0.3rem 0.65rem',
            borderRadius: 'var(--radius-full)',
            background: isWsConnected ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
            color: isWsConnected ? 'var(--accent-emerald)' : 'var(--accent-amber)',
            border: `1px solid ${isWsConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
          }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: isWsConnected ? 'var(--accent-emerald)' : 'var(--accent-amber)',
            }} />
            <span>{isWsConnected ? 'LIVE STREAM' : 'POLLING MODE'}</span>
          </div>

          {/* New shipment button */}
          <button
            onClick={onOpenCreateModal}
            className="btn btn-primary"
            style={{ fontSize: '0.8rem', padding: '0.45rem 0.85rem' }}
          >
            + New Shipment
          </button>
        </div>
      </header>

      {/* Mandatory Safety Notice / Simulation Disclaimer Banner */}
      <div className="disclaimer-banner">
        <span>⚠️</span>
        <span>
          <b>[SIMULATION NOTICE]</b> This is an interactive hackathon demonstration. Outputs are simulated illustrative models and are <b>not validated</b> for real biologic release or clinical decision-making.
        </span>
      </div>
    </>
  );
};
