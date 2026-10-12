import React, { useState } from 'react';
import { api } from '../services/api';
import type { NFCTransfer } from '../types/domain';

interface NFCTransferModalProps {
  shipmentId: string;
  isOpen: boolean;
  onClose: () => void;
  onTransferComplete?: (transfer: NFCTransfer) => void;
}

export const NFCTransferModal: React.FC<NFCTransferModalProps> = ({
  shipmentId,
  isOpen,
  onClose,
  onTransferComplete,
}) => {
  const [status, setStatus] = useState<'idle' | 'scanning' | 'transferring' | 'success' | 'failed'>('idle');
  const [transferData, setTransferData] = useState<NFCTransfer | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleStartTransfer = async () => {
    setStatus('scanning');
    setErrorMessage(null);

    // Simulate contactless scan detection delay
    setTimeout(async () => {
      setStatus('transferring');
      try {
        const result = await api.triggerNFCTransfer(shipmentId);
        setTransferData(result);
        setStatus('success');
        onTransferComplete?.(result);
      } catch (e: any) {
        setStatus('failed');
        setErrorMessage(e.message || 'Simulated NFC transfer failed');
      }
    }, 1200);
  };

  const handleReset = () => {
    setStatus('idle');
    setTransferData(null);
    setErrorMessage(null);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px' }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.4rem' }}>📱</span>
            <div>
              <h3 style={{ fontSize: '1.1rem' }}>Simulated NFC Package Handoff</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Contactless package data verification & chain-of-custody handoff
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

        {/* Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '1.25rem' }}>
          {status === 'idle' && (
            <>
              <div style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'rgba(6, 182, 212, 0.1)',
                border: '2px dashed var(--accent-cyan)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.5rem',
              }}>
                📶
              </div>
              <div>
                <h4 style={{ fontSize: '1.05rem', marginBottom: '0.35rem' }}>Ready for NFC Interrogation</h4>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', maxWidth: '380px' }}>
                  Simulates extracting tamper-evident cold-chain logs directly from the smart shipper's virtual NFC tag into the facility receiver node.
                </p>
              </div>
              <button onClick={handleStartTransfer} className="btn btn-primary" style={{ padding: '0.65rem 1.5rem' }}>
                Tap Virtual NFC Tag
              </button>
            </>
          )}

          {status === 'scanning' && (
            <>
              <div style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.5rem',
                animation: 'pulse-ring 1.2s infinite',
              }}>
                🔍
              </div>
              <div>
                <h4 style={{ fontSize: '1.05rem', marginBottom: '0.35rem' }}>Scanning Field...</h4>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  Interrogating 13.56 MHz virtual tag frequency for shipment {shipmentId}...
                </p>
              </div>
            </>
          )}

          {status === 'transferring' && (
            <>
              <div style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'rgba(139, 92, 246, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.5rem',
                animation: 'pulse-ring 1.2s infinite',
              }}>
                ⚡
              </div>
              <div>
                <h4 style={{ fontSize: '1.05rem', marginBottom: '0.35rem' }}>Transferring Sensor Stream...</h4>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  Extracting cryptographic thermal logs and excursion records to server...
                </p>
              </div>
            </>
          )}

          {status === 'success' && transferData && (
            <>
              <div style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '2px solid var(--accent-emerald)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.5rem',
              }}>
                ✅
              </div>
              <div>
                <h4 style={{ fontSize: '1.1rem', color: 'var(--accent-emerald)', marginBottom: '0.35rem' }}>
                  Handoff Transfer Succeeded
                </h4>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', maxWidth: '380px' }}>
                  {transferData.message}
                </p>
              </div>

              <div style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                textAlign: 'left',
                fontSize: '0.8rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Transfer ID:</span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{transferData.id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Records Extracted:</span>
                  <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{transferData.records_transferred} observations</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Audit Verified:</span>
                  <span style={{ color: 'var(--accent-emerald)' }}>✓ Appended to audit log</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button onClick={handleReset} className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                  Run Another Scan
                </button>
                <button onClick={onClose} className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
                  Done
                </button>
              </div>
            </>
          )}

          {status === 'failed' && (
            <>
              <div style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '2px solid var(--accent-rose)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.5rem',
              }}>
                ❌
              </div>
              <div>
                <h4 style={{ fontSize: '1.05rem', color: 'var(--accent-rose)', marginBottom: '0.35rem' }}>
                  Handoff Encountered Error
                </h4>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  {errorMessage || 'Unable to complete simulated contactless exchange.'}
                </p>
              </div>
              <button onClick={handleReset} className="btn btn-secondary">
                Retry Handoff
              </button>
            </>
          )}

          {/* Educational Disclaimer */}
          <div style={{
            fontSize: '0.725rem',
            color: 'var(--text-dim)',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '0.75rem',
            width: '100%',
          }}>
            Simulation Notice: Software emulation of physical cold-chain NFC data transfer for demonstration purposes.
          </div>
        </div>
      </div>
    </div>
  );
};
