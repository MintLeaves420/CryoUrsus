# CryoUrsus --- API Contract (MVP)

Base URL during local development: `http://127.0.0.1:8000/api`

Use JSON over HTTP for commands and snapshots, and WebSockets for live
events. Exact endpoint names may be adjusted to match an existing
codebase, but update this document and frontend types together.

## 1. Health and profiles

### `GET /health`

Returns backend and database readiness.

### `GET /profiles`

Returns configured product profiles and whether each is illustrative or
verified-source.

### `GET /profiles/{profile_id}`

Returns one profile.

## 2. Shipments

### `GET /shipments`

Query parameters may include `status`, `profile_id`, `limit`, and
`offset`.

### `POST /shipments`

Example request:

``` json
{
  "profile_id": "demo-profile-a",
  "vial_count": 9,
  "sensor_count": 4,
  "scenario": "normal",
  "destination_label": "Demo destination"
}
```

Returns the created shipment, sensors, profile summary, and simulation
label.

### `GET /shipments/{shipment_id}`

Returns shipment metadata, status, profile, sensor health, active
alerts, summary features, demo estimate if available, and operator
assessment.

### `POST /shipments/{shipment_id}/start`

Starts one simulation task. Idempotency should prevent duplicate tasks.

### `POST /shipments/{shipment_id}/pause`

Pauses generation without ending the shipment.

### `POST /shipments/{shipment_id}/resume`

Resumes a paused simulation without creating duplicate tasks.

### `POST /shipments/{shipment_id}/end`

Stops generation and marks the shipment completed.

### `POST /shipments/{shipment_id}/scenario`

Request:

``` json
{
  "scenario": "gradual_warming",
  "parameters": {
    "target_temperature_c": 10.0
  }
}
```

Only accept a whitelist of scenarios and validate all parameters. Use
illustrative values; the example target is not an official product
limit.

## 3. Readings and events

### `GET /shipments/{shipment_id}/readings`

Supports `limit`, `since`, and/or time range filters. Return
newest/oldest order explicitly.

### `GET /shipments/{shipment_id}/events`

Returns excursion events, sensor-health events, and audit events in
chronological order.

### `GET /shipments/{shipment_id}/summary`

Returns peak/minimum, valid-data coverage, excursion duration, crossing
count, rate-of-change features, and current data-quality status.

## 4. Alerts

### `GET /alerts`

Supports shipment and status filters.

### `POST /alerts/{alert_id}/acknowledge`

Acknowledges an alert and writes an audit event.

Alert creation and state transitions are performed by backend services,
not trusted to the browser.

## 5. Assessment

### `GET /shipments/{shipment_id}/assessment`

Returns the current demo estimate and any operator review.

### `POST /shipments/{shipment_id}/assessment`

Example request:

``` json
{
  "review_status": "reviewed",
  "reviewer_label": "Demo operator",
  "review_note": "Reviewed the simulated upper-limit event."
}
```

The backend may calculate/update the illustrative estimate separately
from the human review status. Never accept a client-submitted score as
an authoritative backend prediction.

## 6. Simulated NFC

### `POST /shipments/{shipment_id}/nfc-transfer`

Starts a simulated transfer, persists transfer status, and returns the
transfer ID. If transfer is represented asynchronously, expose a status
endpoint.

### `GET /nfc-transfers/{transfer_id}`

Returns the transfer state and number of records transferred.

This endpoint does not communicate with physical NFC hardware.

## 7. Reports

### `GET /shipments/{shipment_id}/report.pdf`

Returns a PDF with `Content-Type: application/pdf` and a sensible
download filename. Include the simulation disclaimer and profile
provenance.

## 8. WebSocket

Connect to:

`ws://127.0.0.1:8000/api/ws/shipments/{shipment_id}`

Example message envelope:

``` json
{
  "type": "reading.created",
  "version": 1,
  "shipment_id": "shp_example",
  "timestamp": "2026-10-13T12:00:00Z",
  "data": {
    "sensor_id": "sensor-1",
    "temperature_c": 4.2,
    "quality_status": "valid"
  }
}
```

Potential message types: - `shipment.status_changed` -
`reading.created` - `sensor.health_changed` - `excursion.started` -
`excursion.updated` - `excursion.ended` - `alert.created` -
`alert.updated` - `assessment.updated` - `nfc.transfer_updated`

Persist state before broadcasting. Clients should fetch a fresh REST
snapshot after reconnecting. The UI must show a disconnected/stale state
when the stream is unavailable.

## 9. Error format

Prefer a consistent response such as:

``` json
{
  "error": {
    "code": "invalid_state",
    "message": "A completed shipment cannot be resumed."
  }
}
```

Use standard HTTP status codes: 400 for invalid request/state, 404 for
missing records, 409 for conflicting lifecycle actions, and 500 for
unexpected server errors. Never expose stack traces to the client.

## 10. API invariants

-   All IDs are stable and unique.
-   All timestamps are ISO 8601 UTC.
-   Temperature fields use Celsius and include explicit names such as
    `temperature_c`.
-   All sample data are marked simulated.
-   Only one simulation loop can run per shipment.
-   A sensor fault is not automatically a temperature excursion.
-   A disconnected or invalid reading must not be silently treated as an
    in-range reading.
