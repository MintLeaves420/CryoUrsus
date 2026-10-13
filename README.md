# CryoUrsus --- Project Documentation

CryoUrsus is a hackathon demo of an explainable cold-chain monitoring
workflow. It simulates package temperatures, detects excursions and
sensor faults, presents a demonstration-only viability estimate,
synchronizes Truck / Operator / Owner views, simulates NFC handoff, and
generates a PDF report.

**Important:** This project is a simulation. It is not a validated
cold-chain monitoring device and must not be used to decide whether real
biologics are safe for use.

## Documentation index

-   `Docs\PRD.md` --- product vision, users, features, non-goals, acceptance
    criteria.
-   `Docs\rules.md` --- coding-agent operating rules and quality/safety
    constraints.
-   `Docs\software-architecture.md` --- system components, data flow,
    simulation, real-time events, decisions.
-   `Docs\ML_PIPELINE.md` --- machine learning regression architecture, temperature grades, features, and SHAP explainability.
-   `Docs\data-model.md` --- logical SQLite entities, fields, relationships,
    and status semantics.
-   `Docs\API.md` --- proposed REST/WebSocket contract.
-   `Docs\IMPLEMENTATION_PLAN.md` --- incremental build sequence and judge
    demo script.

## Recommended implementation stack

-   React + TypeScript + Vite
-   Three.js / React Three Fiber for the 3D package scene
-   FastAPI + Pydantic
-   Scikit-Learn + SHAP + Joblib (Offline ML Viability & Explainability)
-   SQLite
-   Recharts
-   ReportLab for PDF generation

Inspect the existing repository before installing dependencies or
creating a new structure. Keep the implementation consistent with
working starter code where possible.

## Local development

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+

### Train the ML Model (Offline / On-Demand)
```powershell
# Trains Random Forest regressor and outputs backend/ml/artifacts/viability_model.joblib
.\backend\venv\Scripts\python backend\ml\train_model.py
```

### Backend Setup & Run
```powershell
# In project root:
.\backend\venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```
Backend API will be live at `http://127.0.0.1:8000/api`.
Interactive OpenAPI docs: `http://127.0.0.1:8000/docs`.

### Run Backend Tests
```powershell
$env:PYTHONPATH="."; .\backend\venv\Scripts\pytest backend\tests
```

### Frontend Setup & Run
```powershell
cd frontend
npm run dev
```
Frontend will be live at `http://localhost:5173`.

### Frontend Build
```powershell
cd frontend
npm run build
```

## Demo principles

-   Use clearly labelled illustrative profiles.
-   Show units and timestamps.
-   Keep sensor faults distinct from temperature excursions.
-   Explain demo-estimate inputs and method version.
-   Keep all dashboard views synchronized through backend records.
-   Include the simulation disclaimer in the UI and downloadable
    reports.
