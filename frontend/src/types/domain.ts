export interface ProductProfile {
  id: string;
  name: string;
  category?: string;
  lower_limit_c: number;
  upper_limit_c: number;
  profile_kind: 'illustrative' | 'verified_source';
  source_name?: string;
  source_version?: string;
  source_date?: string;
  notes?: string;
  demo_model_version?: string;
  demo_parameters_json?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Sensor {
  id: string;
  shipment_id: string;
  label: string;
  position_x: number;
  position_y: number;
  position_z: number;
  health_status: 'healthy' | 'stuck' | 'disconnected' | 'implausible' | 'stale';
  last_valid_temperature_c?: number | null;
  last_reading_at?: string | null;
  created_at: string;
}

export interface Shipment {
  id: string;
  profile_id: string;
  status: 'created' | 'running' | 'paused' | 'completed' | 'review_required';
  vial_count: number;
  sensor_count: number;
  destination_label?: string | null;
  scenario: string;
  started_at?: string | null;
  ended_at?: string | null;
  created_at: string;
  updated_at: string;
  operator_review_status?: string | null;
  operator_review_note?: string | null;
  profile?: ProductProfile;
  sensors: Sensor[];
  active_alerts_count: number;
  demo_disclaimer?: string;
}

export interface Reading {
  id: number;
  shipment_id: string;
  sensor_id: string;
  timestamp: string;
  temperature_c?: number | null;
  quality_status: 'valid' | 'stuck' | 'disconnected' | 'implausible' | 'stale';
  source: string;
  scenario?: string;
  created_at: string;
}

export interface Alert {
  id: string;
  shipment_id: string;
  sensor_id?: string | null;
  excursion_event_id?: string | null;
  type: 'upper_limit' | 'lower_limit' | 'sensor_fault' | 'data_quality';
  severity: 'info' | 'warning' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  title: string;
  message: string;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string | null;
}

export interface ExcursionEvent {
  id: string;
  shipment_id: string;
  sensor_id: string;
  direction: 'upper' | 'lower';
  status: 'active' | 'resolved';
  started_at: string;
  last_breach_at: string;
  ended_at?: string | null;
  duration_seconds?: number;
  peak_temperature_c?: number;
  minimum_temperature_c?: number;
  crossing_count: number;
  exposure_degree_minutes?: number;
}

export interface ShipmentSummary {
  shipment_id: string;
  status: string;
  total_readings: number;
  valid_readings_count: number;
  valid_data_coverage: number;
  peak_temperature_c?: number | null;
  minimum_temperature_c?: number | null;
  excursion_duration_seconds: number;
  crossing_count: number;
  max_rate_c_per_minute: number;
  data_quality_status: string;
  sensors_summary: any[];
  demo_score?: number | null;
  demo_label?: string | null;
  explanation: string[];
  method_version: string;
  disclaimer: string;
}

export interface Assessment {
  id?: string;
  shipment_id: string;
  review_status: string;
  review_note?: string | null;
  reviewer_label?: string | null;
  created_at?: string;
  method_version: string;
  demo_score?: number | null;
  demo_label?: string | null;
  features?: any;
  explanation?: string[];
  disclaimer: string;
}

export interface NFCTransfer {
  id: string;
  shipment_id: string;
  status: 'started' | 'success' | 'failed';
  records_transferred: number;
  started_at: string;
  completed_at?: string | null;
  message?: string | null;
  simulation_label: string;
}
