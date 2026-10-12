import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { ProductProfile, Shipment, Reading, Alert, ShipmentSummary, Assessment } from './types/domain';
import { api } from './services/api';
import { ShipmentWebSocketClient } from './services/websocket';
import { Header } from './components/Header';
import { TruckDashboard } from './pages/TruckDashboard';
import { OperatorDashboard } from './pages/OperatorDashboard';
import { OwnerDashboard } from './pages/OwnerDashboard';
import { CreateShipmentModal } from './components/CreateShipmentModal';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'truck' | 'operator' | 'owner'>('truck');
  const [profiles, setProfiles] = useState<ProductProfile[]>([]);
  const [currentShipment, setCurrentShipment] = useState<Shipment | null>(null);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<ShipmentSummary | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const wsClientRef = useRef<ShipmentWebSocketClient | null>(null);

  // Load profiles and initial active shipment
  const initializeApp = async () => {
    try {
      setIsLoading(true);
      const fetchedProfiles = await api.getProfiles();
      setProfiles(fetchedProfiles);

      const existingShipments = await api.getShipments({ limit: 10 });
      let activeShipment: Shipment;

      if (existingShipments.length > 0) {
        activeShipment = existingShipments[0];
      } else {
        // Automatically seed an initial demo shipment if none exist
        activeShipment = await api.createShipment({
          profile_id: fetchedProfiles[0]?.id || 'demo-profile-standard-mab',
          vial_count: 9,
          sensor_count: 4,
          scenario: 'normal',
          destination_label: 'Judge Demo Facility (Lab Alpha)',
        });
      }

      setCurrentShipment(activeShipment);
      await loadShipmentData(activeShipment.id);
    } catch (e) {
      console.error('Initialization error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadShipmentData = useCallback(async (shipmentId: string) => {
    try {
      const [shp, readingsData, alertsData, summaryData, assessmentData] = await Promise.all([
        api.getShipment(shipmentId),
        api.getReadings(shipmentId, 100),
        api.getAlerts(shipmentId),
        api.getSummary(shipmentId),
        api.getAssessment(shipmentId).catch(() => null),
      ]);

      setCurrentShipment(shp);
      setReadings(readingsData.readings);
      setAlerts(alertsData);
      setSummary(summaryData);
      setAssessment(assessmentData);
    } catch (e) {
      console.warn('Error loading shipment data:', e);
    }
  }, []);

  // Connect WebSocket to active shipment
  useEffect(() => {
    if (!currentShipment?.id) return;

    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
    }

    const client = new ShipmentWebSocketClient(currentShipment.id, (connected) => {
      setIsWsConnected(connected);
    });

    const unsubscribe = client.subscribe((event) => {
      if (event.type === 'reading.created' && event.data) {
        const newReading: Reading = {
          id: event.data.id || Date.now(),
          shipment_id: currentShipment.id,
          sensor_id: event.data.sensor_id,
          timestamp: event.timestamp || new Date().toISOString(),
          temperature_c: event.data.temperature_c,
          quality_status: event.data.quality_status || 'valid',
          source: 'simulated',
          created_at: event.timestamp || new Date().toISOString(),
        };

        setReadings((prev) => [newReading, ...prev.slice(0, 99)]);

        // Update sensor in current shipment
        setCurrentShipment((prev) => {
          if (!prev) return prev;
          const updatedSensors = prev.sensors.map((s) => {
            if (s.id === event.data.sensor_id) {
              return {
                ...s,
                last_valid_temperature_c:
                  event.data.is_valid && event.data.temperature_c !== null
                    ? event.data.temperature_c
                    : s.last_valid_temperature_c,
                health_status: event.data.quality_status,
                last_reading_at: event.timestamp,
              };
            }
            return s;
          });
          return { ...prev, sensors: updatedSensors };
        });
      } else if (event.type === 'alert.created' || event.type === 'alert.updated' || event.type === 'excursion.started') {
        // Refresh alerts and summary
        api.getAlerts(currentShipment.id).then(setAlerts).catch(console.error);
        api.getSummary(currentShipment.id).then(setSummary).catch(console.error);
      } else if (event.type === 'shipment.status_changed' && event.data?.status) {
        setCurrentShipment((prev) => (prev ? { ...prev, status: event.data.status } : prev));
      } else if (event.type === 'assessment.updated') {
        api.getAssessment(currentShipment.id).then(setAssessment).catch(console.error);
      }
    });

    client.connect();
    wsClientRef.current = client;

    // Polling fallback to keep summary & alerts synced even if WebSocket drops
    const pollInterval = setInterval(() => {
      if (currentShipment?.id) {
        api.getSummary(currentShipment.id).then(setSummary).catch(() => {});
        api.getAlerts(currentShipment.id).then(setAlerts).catch(() => {});
      }
    }, 3000);

    return () => {
      unsubscribe();
      client.disconnect();
      clearInterval(pollInterval);
    };
  }, [currentShipment?.id]);

  useEffect(() => {
    initializeApp();
  }, []);

  const handleSelectShipment = (shipmentId: string) => {
    loadShipmentData(shipmentId);
    setActiveTab('truck');
  };

  const handleShipmentCreated = (newShipment: Shipment) => {
    setCurrentShipment(newShipment);
    loadShipmentData(newShipment.id);
    setActiveTab('truck');
  };

  if (isLoading || !currentShipment) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem',
      }}>
        <div style={{ fontSize: '3rem', animation: 'pulse-ring 1.5s infinite' }}>🐻‍❄️</div>
        <h2 style={{ fontSize: '1.25rem', color: 'var(--text-main)' }}>Initializing CryoUrsus Telemetry...</h2>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>Loading SQLite database and cold-chain models</span>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isWsConnected={isWsConnected}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        currentShipmentId={currentShipment.id}
      />

      <main style={{ flex: 1, padding: '1.5rem 2rem', maxWidth: '1600px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'truck' && (
          <TruckDashboard
            shipment={currentShipment}
            readings={readings}
            alerts={alerts}
            summary={summary}
            onShipmentUpdated={setCurrentShipment}
            onAlertsChanged={() => loadShipmentData(currentShipment.id)}
          />
        )}

        {activeTab === 'operator' && (
          <OperatorDashboard
            shipment={currentShipment}
            readings={readings}
            alerts={alerts}
            summary={summary}
            assessment={assessment}
            onShipmentUpdated={setCurrentShipment}
            onAlertsChanged={() => loadShipmentData(currentShipment.id)}
            onAssessmentUpdated={setAssessment}
          />
        )}

        {activeTab === 'owner' && (
          <OwnerDashboard
            currentShipmentId={currentShipment.id}
            onSelectShipment={handleSelectShipment}
            onOpenCreateModal={() => setIsCreateModalOpen(true)}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '1rem 2rem',
        fontSize: '0.75rem',
        color: 'var(--text-dim)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(5, 11, 20, 0.9)',
      }}>
        <div>
          <span>CryoUrsus Explainable Cold-Chain Decision Support</span>
          <span style={{ margin: '0 8px' }}>•</span>
          <span>FastAPI + SQLite + React 3D</span>
        </div>
        <div style={{ color: '#fde68a' }}>
          Simulated Demonstration Only — Not Validated for Real Biologics Release
        </div>
      </footer>

      {/* Shipment Creation Modal */}
      <CreateShipmentModal
        profiles={profiles}
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onShipmentCreated={handleShipmentCreated}
      />
    </div>
  );
};

export default App;
