# CryoUrsus — Codebase Status, Architecture & Implementation Guide

> **Document Status:** Comprehensive architectural and operational status reference  
> **Audience:** Future AI agents, developers, reviewers, and evaluators  
> **Target System:** CryoUrsus Cold-Chain Telemetry & Decision-Support Simulation Platform  
> **Repository Root:** `.\Downloads\CryoUrsus`

---

## 1. Executive Summary & Purpose

CryoUrsus is a specialized web-based application simulating an explainable, auditable cold-chain monitoring system for temperature-sensitive biologics (e.g., monoclonal antibodies, mRNA vaccines, insulin). 

The application solves key operational challenges in biologics logistics:
1. Continuous multi-sensor virtual thermal telemetry with 3D physical package visualization.
2. Real-time deterministic excursion detection (breach direction, exposure degree-minutes, event transitions).
3. Sensor fault disambiguation (differentiating sensor failure—stuck, disconnected, implausible—from true biological temperature excursions).
4. Explainable, demonstrative viability estimation with transparent mathematical feature extraction.
5. Multi-role synchronization across three primary views:
   - **Truck / Package Simulator** (telemetry controls, manual override, 3D vial matrix, live charts)
   - **Operator Dashboard** (excursion timeline, explainability breakdown, human disposition review)
   - **Owner / Logistics Manager Dashboard** (fleet overview, active alerts, audit trails)
6. Simulated NFC chain-of-custody handoff and automated PDF compliance report generation.

> [!IMPORTANT]
> **Simulation Disclaimer:**  
> CryoUrsus is strictly an interactive simulation for demonstration, evaluation, and hackathon decision-support workflows. It does **not** connect to physical hardware sensors and is **not** validated for clinical release or real biological disposal.

---

## 2. System Architecture & Tech Stack

```mermaid
graph TD
    subgraph Frontend [React 19 + TypeScript + Vite]
        UI_Header[Navigation Header & Mode Switcher]
        UI_Truck[Truck Dashboard + 3D Three.js Package Scene]
        UI_Operator[Operator Dashboard + XAI Explanation Panel]
        UI_Owner[Owner Dashboard + Fleet Overview]
        UI_Shared[AlertBanner, TemperatureChart, ReadingsTable]
        API_Client[REST Client (fetch) & WebSocket Manager]
    end

    subgraph Backend [FastAPI + Python 3.10+]
        Main[FastAPI main.py + Lifespan]
        WS[WebSocket Manager ws_manager]
        
        subgraph APILayer [API Routes /api]
            R_Prof[routes_profiles.py]
            R_Ship[routes_shipments.py]
            R_Read[routes_readings.py]
            R_Alert[routes_alerts.py]
            R_NFC[routes_nfc.py]
        end
        
        subgraph CoreServices [Business Services]
            SimSvc[simulation_service.py (Async Tick Lifecycle)]
            SensorVal[sensor_validation.py (Data Quality Filter)]
            ExcEng[excursion_engine.py (Continuous Breach Tracker)]
            ViabEst[viability_estimator.py (Deterministic XAI Scorer)]
            RepSvc[report_service.py (ReportLab PDF Generator)]
            AuditSvc[audit_service.py (Immutable Event Log)]
            NFCSvc[nfc_service.py (Simulated NFC Handshake)]
        end
    end

    subgraph Storage [SQLite persistent database]
        DB[(cryoursus.db)]
        T_Prof[(product_profiles)]
        T_Ship[(shipments)]
        T_Sens[(sensors)]
        T_Read[(readings)]
        T_Exc[(excursion_events)]
        T_Alert[(alerts)]
        T_Ass[(assessments)]
        T_NFC[(nfc_transfers)]
        T_Audit[(audit_events)]
    end

    UI_Header --> API_Client
    UI_Truck --> API_Client
    UI_Operator --> API_Client
    UI_Owner --> API_Client
    API_Client <-->|REST HTTP| APILayer
    API_Client <-->|Live JSON Events| WS

    APILayer --> CoreServices
    SimSvc --> SensorVal
    SensorVal --> ExcEng
    ExcEng --> ViabEst
    CoreServices --> DB
    WS --> UI_Shared
```

### Core Technologies
- **Backend:**
  - Python (tested on Python 3.14 / 3.10+)
  - **FastAPI** (`fastapi>=0.110.0`) with **Uvicorn**
  - **Pydantic v2** (`pydantic>=2.6.0`) for request/response serialization
  - **SQLite3** for zero-configuration, ACID-compliant persistence
  - **ReportLab** (`reportlab>=4.1.0`) for pixel-perfect PDF document generation
  - **pytest** + **httpx** for integration and unit test automation
- **Frontend:**
  - **React 19** (`react@^19.2.8`, `react-dom@^19.2.8`)
  - **TypeScript** (`~6.0.2`) + **Vite 8**
  - **Three.js** & **React Three Fiber** (`@react-three/fiber@^9.8.1`, `@react-three/drei@^10.7.9`) for 3D vial package scene
  - **Recharts** (`recharts@^3.10.1`) for responsive 2D dual-threshold temperature graphs
  - **Lucide React** for modern UI icons
  - Custom design tokens in `frontend/src/index.css` (Glassmorphism, dark polar-technical palette)

---

## 3. Directory Layout & Key Modules

```text
CryoUrsus/
├── README.md                           # Quickstart and run instructions
├── .env.example                        # Environment variable configuration template
├── Docs/                               # Specification & status documentation
│   ├── PRD.md                          # Product Requirements Document
│   ├── rules.md                        # Coding agent guidelines & architectural constraints
│   ├── software-architecture.md        # Architectural decisions and data flows
│   ├── data-model.md                   # SQLite schemas, relationships, and indices
│   ├── API.md                          # REST & WebSocket contract specifications
│   ├── IMPLEMENTATION_PLAN.md          # 7-phase implementation checklist
│   └── CODEBASE_STATUS.md              # THIS FILE: Current status, guide & architecture
├── backend/
│   ├── requirements.txt                # Python dependencies
│   ├── app/
│   │   ├── main.py                     # App entry point, CORS, lifespan, WS route, error handling
│   │   ├── config.py                   # Global constants, DB path, CORS origins, demo disclaimers
│   │   ├── api/                        # HTTP & WebSocket route handlers
│   │   │   ├── routes_profiles.py      # GET /api/profiles, GET /api/profiles/{id}
│   │   │   ├── routes_shipments.py     # Shipment CRUD, lifecycle controls (start/pause/resume/end),
│   │   │   │                           # scenarios, events, summary, PDF endpoint
│   │   │   ├── routes_readings.py      # Historical telemetry readings queries
│   │   │   ├── routes_alerts.py        # Active alerts listing, acknowledgement endpoints
│   │   │   ├── routes_nfc.py           # Simulated NFC transfer trigger and status queries
│   │   │   └── websocket.py            # ConnectionManager broadcasting live updates
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database.py             # SQLite DDL migrations, indices, seeds, connection pool
│   │   ├── schemas/                    # Pydantic v2 schemas for all payloads
│   │   │   ├── alert.py, assessment.py, nfc.py, profile.py,
│   │   │   └── reading.py, shipment.py, summary.py
│   │   └── services/                   # Modular domain logic
│   │       ├── shipment_service.py     # Shipment state management and DB transactions
│   │       ├── simulation_service.py   # Async tick loop, thermal scenario generators, manual overrides
│   │       ├── sensor_validation.py    # Stuck, disconnected, out-of-range sensor validations
│   │       ├── excursion_engine.py     # Upper/lower limit tracking, continuous exposure degree-minutes
│   │       ├── viability_estimator.py  # Deterministic XAI estimator & natural language explainability
│   │       ├── alert_service.py        # Alert lifecycle, deduplication, resolution
│   │       ├── audit_service.py        # Append-only audit events table
│   │       ├── nfc_service.py          # Simulated NFC transfer state machine
│   │       └── report_service.py       # ReportLab PDF generator compiling telemetry and review
│   └── tests/
│       ├── test_health.py              # Health check endpoint verification
│       ├── test_profiles_and_shipments.py
│       ├── test_excursions_and_sensors.py
│       ├── test_viability_and_nfc.py
│       └── test_live_e2e.py            # End-to-end simulation lifecycle & report PDF test
└── frontend/
    ├── package.json                    # NPM dependencies and scripts
    ├── vite.config.ts                  # Vite bundler configuration
    ├── index.html                      # Entry HTML with Inter fonts
    └── src/
        ├── main.tsx                    # React DOM mounting
        ├── App.tsx                     # Top-level state coordinator, WS subscriber, polling fallback
        ├── index.css                   # Global CSS design system and color tokens
        ├── types/domain.ts             # TypeScript definitions matching backend schemas
        ├── services/
        │   ├── api.ts                  # Fetch-based REST API client
        │   └── websocket.ts            # Resilient WebSocket client with reconnect handling
        ├── pages/
        │   ├── TruckDashboard.tsx      # 3D package, controls, scenario switcher, readings chart
        │   ├── OperatorDashboard.tsx   # Excursions breakdown, explainability panel, review modal
        │   └── OwnerDashboard.tsx      # Fleet shipment cards, active alerts summary, filter controls
        └── components/
            ├── Header.tsx              # Top bar, active view switcher, WS connection indicator
            ├── Package3D.tsx           # React Three Fiber 3D vial & sensor matrix
            ├── TemperatureChart.tsx    # Dual-threshold Recharts thermal line chart
            ├── ReadingsTable.tsx       # Live scrollable sensor data table
            ├── SimulationControls.tsx  # Start, Pause, Resume, End, Scenario select, Temp slider
            ├── ExplanationPanel.tsx    # Explainable AI factors, model method version, disclaimer
            ├── AlertBanner.tsx         # Real-time alert notifications with acknowledge button
            ├── CreateShipmentModal.tsx # New shipment configuration modal
            └── NFCTransferModal.tsx    # Multi-step animated NFC transfer simulation modal
```

---

## 4. Current Implementation Status vs. Implementation Plan

All 7 core architectural phases specified in [Docs/IMPLEMENTATION_PLAN.md](file:///c:/Users/Naaziya/Downloads/CryoUrsus/Docs/IMPLEMENTATION_PLAN.md) are **fully implemented** in code:

| Phase | Description | Implementation Status | Key Components & Files |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Baseline & Inspection | ✅ **Complete** | `.gitignore`, `.env.example`, `README.md`, folder structure established. |
| **Phase 1** | Domain Foundation | ✅ **Complete** | SQLite database schemas (`database.py`), seed profiles (mAbs, mRNA, Insulin), CRUD API endpoints, error handling. |
| **Phase 2** | Truck Simulator | ✅ **Complete** | Async background simulation loop (`simulation_service.py`), 3D vial scene (`Package3D.tsx`), `TemperatureChart.tsx`, `ReadingsTable.tsx`. |
| **Phase 3** | Excursions & Alerts | ✅ **Complete** | Sensor validation (`sensor_validation.py`), continuous excursion tracker (`excursion_engine.py`), deduplicating alert service, WebSocket notifications. |
| **Phase 4** | Demo Viability & XAI | ✅ **Complete** | Deterministic mathematical scoring (`viability_estimator.py`), natural-language explanation generation, insufficient-data handling. |
| **Phase 5** | Dashboards | ✅ **Complete** | Coordinated views for Truck, Operator, and Owner; shared backend state; assessment review submission form. |
| **Phase 6** | Simulated NFC & Reports | ✅ **Complete** | NFC transfer state machine (`nfc_service.py`, `NFCTransferModal.tsx`), ReportLab PDF report generation (`report_service.py`). |
| **Phase 7** | Presentation Polish | ✅ **Complete** | Refined glassmorphism styling, alert banners, manual temperature slider overrides, explicit simulation notices. |

---

## 5. Domain Logic & Data Model Details

### 5.1 Product Profiles & Seeds
Seeded in `backend/app/models/database.py`:
1. `demo-profile-standard-mab` (**Standard Monoclonal Antibody**): 2.0°C to 8.0°C
2. `demo-profile-mrna-ultra-cold` (**mRNA Ultra-Cold Biologic**): -80.0°C to -60.0°C
3. `demo-profile-insulin-cool` (**Insulin Cool Storage**): 2.0°C to 15.0°C

### 5.2 Sensor Validation Engine (`sensor_validation.py`)
Validates every incoming raw reading before domain analysis:
- **Plausibility Check:** Flagged as `implausible` if reading < -100.0°C or > +80.0°C.
- **Stuck Sensor Check:** Evaluates rolling window of previous 5 readings. If standard deviation is 0.0 with identical floats, flagged as `stuck`.
- **Disconnect Check:** Null reading or disconnected flag marked as `disconnected`.
- **Outcome:** Non-valid readings do **not** trigger temperature excursion alerts; instead, they generate distinct `sensor_health` warnings, maintaining clean separation between thermal breaches and hardware faults.

### 5.3 Excursion Detection Engine (`excursion_engine.py`)
- Compares valid readings against profile `lower_limit_c` and `upper_limit_c`.
- **Continuous Lifecycle:**
  - When a sensor breaches a threshold, an `excursion_events` record is created (`status='active'`).
  - While ongoing, subsequent readings update duration, peak/minimum temperature, and calculate cumulative exposure:
    $$\text{Exposure (degree-minutes)} += |\text{current\_temp} - \text{limit}| \times \frac{\text{tick\_seconds}}{60}$$
  - When temperature returns within safe limits, the active excursion transition closes (`status='resolved'`) and automatically resolves the linked alert.
- **Alert Deduplication:** Consecutive ticks in the same breach update the existing alert rather than generating spam.

### 5.4 Explainable Demo Viability Model (`viability_estimator.py`)
- **Reliability Gate:** If valid reading coverage is below 50%, returns `"insufficient_data"` with explicit explanation.
- **Deterministic Penalty Formula:**
  $$\text{Score} = \max\left(10.0,\, 100.0 - (\text{Exposure}_{\text{deg-min}} \times \text{decay\_rate} + \max(0, \text{crossing\_count} - 1) \times 1.5)\right)$$
- Accompanied by human-readable explanation strings, method version (`demo-v1.0`), and explicit simulation notices.

### 5.5 Database Entities (`data-model.md`)
SQLite stores 9 core tables:
- `product_profiles`, `shipments`, `sensors`, `readings`, `excursion_events`, `alerts`, `assessments`, `nfc_transfers`, `audit_events`.

---

## 6. How to Run, Test, and Develop

### 6.1 Prerequisites
- **Node.js** (v18+) and **npm**
- **Python** (v3.10+)

### 6.2 Running the Backend
From the project root:
```powershell
# 1. Create and activate virtual environment if not already existing
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r backend\requirements.txt

# 3. Start the FastAPI development server
python -m uvicorn backend.app.main:app --reload --port 8000
```
- API Base: `http://127.0.0.1:8000/api`
- Swagger UI / OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### 6.3 Running Backend Tests
Ensure `PYTHONPATH` includes the repository root:
```powershell
# In PowerShell:
$env:PYTHONPATH="."
.\backend\venv\Scripts\pytest backend\tests -v
```
All tests verify:
- Health check endpoints
- Profile and shipment creation and listing
- Temperature excursion and sensor fault separation
- Deterministic viability scoring and simulated NFC lifecycle
- Full end-to-end simulation lifecycle with PDF report verification

### 6.4 Running the Frontend
```powershell
cd frontend
# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Frontend application URL: `http://localhost:5173`

> [!TIP]
> **Windows PowerShell Execution Policy Note:**  
> If PowerShell blocks `npm` scripts due to execution policy, run npm commands via cmd:  
> `cmd /c "npm run dev"` or `cmd /c "npm run build"`.

---

## 7. Guidelines for Future AI Agents & Developers

1. **Maintain Single Source of Truth:**
   - Always treat FastAPI and SQLite as authoritative. Do not maintain separate in-memory shipment states on the client that diverge from the backend.
2. **Preserve the Simulation Disclaimer:**
   - Any new view, export format, or notification banner must clearly display the disclaimer:
     `"Simulated Demonstration Only — Not Validated for Real Biologics Release"`.
3. **Keep Sensor Faults and Excursions Distinct:**
   - Never classify sensor dropouts, stuck values, or implausible telemetry as temperature breaches. Treat them via `sensor_validation.py` and `sensor_health` alerts.
4. **Deterministic XAI Rules:**
   - Do not replace the explainable viability model with opaque black-box machine learning without retaining transparent feature logging and fallback explainability strings.
5. **Real-Time Synchronization:**
   - When emitting changes to shipments, alerts, or readings, ensure `ws_manager.broadcast()` is dispatched after SQLite commit so all connected tabs (Truck, Operator, Owner) synchronize seamlessly.
