import type {
  ProductProfile,
  Shipment,
  Reading,
  Alert,
  ShipmentSummary,
  Assessment,
  NFCTransfer,
} from '../types/domain';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errMessage = `HTTP Error ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.error?.message) {
        errMessage = errJson.error.message;
      }
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }

  return res.json();
}

export const api = {
  // Health
  checkHealth: () => request<{ status: string; disclaimer: string }>('/health'),

  // Profiles
  getProfiles: () => request<ProductProfile[]>('/profiles'),
  getProfile: (profileId: string) => request<ProductProfile>(`/profiles/${profileId}`),

  // Shipments
  getShipments: (params?: { status?: string; profile_id?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.profile_id) q.append('profile_id', params.profile_id);
    if (params?.limit) q.append('limit', String(params.limit));
    return request<Shipment[]>(`/shipments?${q.toString()}`);
  },
  getShipment: (shipmentId: string) => request<Shipment>(`/shipments/${shipmentId}`),
  createShipment: (data: {
    profile_id: string;
    vial_count: number;
    sensor_count: number;
    scenario: string;
    destination_label?: string;
  }) => request<Shipment>('/shipments', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Controls
  startShipment: (shipmentId: string) => request<Shipment>(`/shipments/${shipmentId}/start`, { method: 'POST' }),
  pauseShipment: (shipmentId: string) => request<Shipment>(`/shipments/${shipmentId}/pause`, { method: 'POST' }),
  resumeShipment: (shipmentId: string) => request<Shipment>(`/shipments/${shipmentId}/resume`, { method: 'POST' }),
  endShipment: (shipmentId: string) => request<Shipment>(`/shipments/${shipmentId}/end`, { method: 'POST' }),
  setScenario: (shipmentId: string, scenario: string) =>
    request<Shipment>(`/shipments/${shipmentId}/scenario`, {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),

  // Readings & Summary
  getReadings: (shipmentId: string, limit: number = 100) =>
    request<{ shipment_id: string; total: number; readings: Reading[] }>(
      `/shipments/${shipmentId}/readings?limit=${limit}&order=desc`
    ),
  getSummary: (shipmentId: string) => request<ShipmentSummary>(`/shipments/${shipmentId}/summary`),
  getEvents: (shipmentId: string) =>
    request<{ shipment_id: string; excursion_events: any[]; audit_events: any[] }>(
      `/shipments/${shipmentId}/events`
    ),

  // Alerts
  getAlerts: (shipmentId?: string, status?: string) => {
    const q = new URLSearchParams();
    if (shipmentId) q.append('shipment_id', shipmentId);
    if (status) q.append('status', status);
    return request<Alert[]>(`/alerts?${q.toString()}`);
  },
  acknowledgeAlert: (alertId: string, acknowledgedBy?: string) =>
    request<Alert>(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: acknowledgedBy || 'operator' }),
    }),

  // Assessment
  getAssessment: (shipmentId: string) => request<Assessment>(`/shipments/${shipmentId}/assessment`),
  submitAssessment: (shipmentId: string, data: { review_status: string; review_note?: string; reviewer_label?: string }) =>
    request<Assessment>(`/shipments/${shipmentId}/assessment`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Simulated NFC
  triggerNFCTransfer: (shipmentId: string) =>
    request<NFCTransfer>(`/shipments/${shipmentId}/nfc-transfer`, { method: 'POST' }),
  getNFCTransfer: (transferId: string) => request<NFCTransfer>(`/nfc-transfers/${transferId}`),

  // PDF Report URL
  getReportPdfUrl: (shipmentId: string) => `${BASE_URL}/shipments/${shipmentId}/report.pdf`,
};
