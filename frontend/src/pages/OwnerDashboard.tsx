import React, { useState, useEffect } from 'react';
import type { Shipment, Alert } from '../types/domain';
import { api } from '../services/api';

interface OwnerDashboardProps {
  currentShipmentId: string;
  onSelectShipment: (shipmentId: string) => void;
  onOpenCreateModal: () => void;
}

export const OwnerDashboard: React.FC<OwnerDashboardProps> = ({
  currentShipmentId,
  onSelectShipment,
  onOpenCreateModal,
}) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [allAlerts, setAllAlerts] = useState<Alert[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const fetchFleetData = async () => {
    try {
      setLoading(true);
      const [shipmentsList, alertsList] = await Promise.all([
        api.getShipments({ limit: 50 }),
        api.getAlerts(),
      ]);
      setShipments(shipmentsList);
      setAllAlerts(alertsList);
    } catch (e) {
      console.error('Failed to fetch owner fleet data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFleetData();
    const interval = setInterval(fetchFleetData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredShipments = shipments.filter((s) => {
    const matchesStatus = filterStatus === 'all' || s.status === filterStatus;
    const matchesSearch =
      s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.destination_label && s.destination_label.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (s.profile?.name && s.profile.name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const activeAlertsCount = allAlerts.filter((a) => a.status === 'active').length;
  const runningCount = shipments.filter((s) => s.status === 'running').length;
  const completedCount = shipments.filter((s) => s.status === 'completed').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Fleet Executive KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem',
      }}>
        <div className="metric-card">
          <span className="metric-label">Total Fleet Monitored</span>
          <span className="metric-value">{shipments.length} Shipments</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            All active demo consignments
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Active Transits</span>
          <span className="metric-value" style={{ color: 'var(--accent-emerald)' }}>
            {runningCount} In Transit
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {completedCount} Finalized & Delivered
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Active Fleet Alerts</span>
          <span className="metric-value" style={{ color: activeAlertsCount > 0 ? 'var(--accent-rose)' : 'var(--text-main)' }}>
            {activeAlertsCount} Alerts
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Requiring operational oversight
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Data Freshness</span>
          <span className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
            1.5s Interval
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Live sync across all clients
          </span>
        </div>
      </div>

      {/* Fleet Controls & Search Filter Bar */}
      <div className="glass-panel" style={{
        padding: '1rem 1.25rem',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
      }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
          <input
            type="text"
            placeholder="Search by ID, product, destination..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input"
            style={{ width: '280px', padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}
          />

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="form-select"
            style={{ width: '160px', padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}
          >
            <option value="all">All Statuses</option>
            <option value="running">In Transit (Running)</option>
            <option value="paused">Paused</option>
            <option value="created">Created</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={fetchFleetData}
            className="btn btn-secondary"
            style={{ fontSize: '0.825rem' }}
          >
            ↻ Refresh
          </button>
          <button
            onClick={onOpenCreateModal}
            className="btn btn-primary"
            style={{ fontSize: '0.825rem' }}
          >
            + Create Shipment
          </button>
        </div>
      </div>

      {/* Shipments Fleet Table */}
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🚚</span>
              <span>Fleet Consignment Overview</span>
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              Cross-dashboard synchronized cold-chain records
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Showing {filteredShipments.length} consignments
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{
                borderBottom: '1px solid var(--border-medium)',
                color: 'var(--text-muted)',
                textAlign: 'left',
              }}>
                <th style={{ padding: '0.65rem 0.8rem' }}>Shipment ID</th>
                <th style={{ padding: '0.65rem 0.8rem' }}>Product Profile</th>
                <th style={{ padding: '0.65rem 0.8rem' }}>Destination</th>
                <th style={{ padding: '0.65rem 0.8rem' }}>Status</th>
                <th style={{ padding: '0.65rem 0.8rem' }}>Active Alerts</th>
                <th style={{ padding: '0.65rem 0.8rem' }}>Operator Review</th>
                <th style={{ padding: '0.65rem 0.8rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredShipments.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
                    {loading ? 'Loading fleet records...' : 'No shipments match the current query.'}
                  </td>
                </tr>
              ) : (
                filteredShipments.map((s) => {
                  const isSelected = s.id === currentShipmentId;
                  const profileName = s.profile?.name || s.profile_id;

                  return (
                    <tr
                      key={s.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        background: isSelected ? 'rgba(6, 182, 212, 0.08)' : 'transparent',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <td style={{ padding: '0.65rem 0.8rem', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {s.id}
                        {isSelected && (
                          <span style={{ marginLeft: '6px', fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>
                            [Active]
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem', maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {profileName}
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem', color: 'var(--text-muted)' }}>
                        {s.destination_label || 'Demo Destination'}
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <span className={`badge ${
                          s.status === 'running'
                            ? 'badge-emerald'
                            : s.status === 'paused'
                            ? 'badge-amber'
                            : s.status === 'completed'
                            ? 'badge-cyan'
                            : 'badge-purple'
                        }`}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        {s.active_alerts_count > 0 ? (
                          <span className="badge badge-rose">
                            🚨 {s.active_alerts_count} Active
                          </span>
                        ) : (
                          <span className="badge badge-emerald">
                            ✓ Clear
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <span className={`badge ${
                          s.operator_review_status === 'reviewed' ? 'badge-emerald' : 'badge-amber'
                        }`}>
                          {s.operator_review_status || 'Pending'}
                        </span>
                      </td>
                      <td style={{ padding: '0.65rem 0.8rem', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => onSelectShipment(s.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                          >
                            Open View
                          </button>
                          <a
                            href={api.getReportPdfUrl(s.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary"
                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', textDecoration: 'none', color: '#fff' }}
                          >
                            PDF
                          </a>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
