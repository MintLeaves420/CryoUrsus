# CryoUrsus — Machine Learning Viability & SHAP Explainability Pipeline

## 1. Overview & Objective
In cold-chain logistics, biological products (e.g. mRNA vaccines, monoclonal antibodies, and cryopreserved cellular therapies) degrade when exposed to temperatures outside their qualified storage envelope.

CryoUrsus replaces rigid heuristics with a **scikit-learn Random Forest regression model** coupled with **SHAP (SHapley Additive exPlanations)** to:
1. Predict remaining product viability percentage (`viability_pct`, between 0.0% and 100.0%).
2. Ingest clinical temperature excursion grades rather than raw temperature values.
3. Quantify feature-level attribution explaining why viability decreased or held stable.
4. Load into memory once on application startup without retraining dynamically during simulations or dashboard refreshes.

---

## 2. Temperature Grade Classification
Rather than feeding raw continuous temperatures directly to the model, telemetry is mapped into excursion grades:

| Grade | Clinical Condition | Thermal Delta Threshold |
|---|---|---|
| **Grade 0** | Normal / Optimal | Inside configured limits $[T_{\min}, T_{\max}]$ |
| **Grade 1** | Mild Excursion | $> 0.0^\circ\text{C}$ up to $2.0^\circ\text{C}$ beyond limits |
| **Grade 2** | Moderate Excursion | $> 2.0^\circ\text{C}$ up to $5.0^\circ\text{C}$ beyond limits |
| **Grade 3** | Severe Excursion | $> 5.0^\circ\text{C}$ beyond limits |

### Directional Breaches:
- **Heat Excursion:** $T > T_{\max}$, with $\Delta = T - T_{\max}$
- **Cold Excursion:** $T < T_{\min}$, with $\Delta = T_{\min} - T$

---

## 3. Feature Engineering Schema
The regression model operates on 16 specific input features derived in seconds (`_sec`):

### Categorical Feature (1):
- `biological_type`: Formulation sensitivity (`monoclonal_antibody`, `mRNA_vaccine`, or `cryopreserved_cell_therapy`).

### Excursion-Grade Durations (9):
- `heat_grade_1_time_sec`: Seconds spent in Heat Grade 1 (mild breach).
- `heat_grade_2_time_sec`: Seconds spent in Heat Grade 2 (moderate breach).
- `heat_grade_3_time_sec`: Seconds spent in Heat Grade 3 (severe breach).
- `cold_grade_1_time_sec`: Seconds spent in Cold Grade 1 (mild breach).
- `cold_grade_2_time_sec`: Seconds spent in Cold Grade 2 (moderate breach).
- `cold_grade_3_time_sec`: Seconds spent in Cold Grade 3 (severe breach).
- `grade_1_time_sec`: Total Grade 1 duration (`heat_grade_1 + cold_grade_1`).
- `grade_2_time_sec`: Total Grade 2 duration (`heat_grade_2 + cold_grade_2`).
- `grade_3_time_sec`: Total Grade 3 duration (`heat_grade_3 + cold_grade_3`).

### Aggregate Event Metrics (6):
- `total_excursion_time_sec`: Cumulative seconds spent in any excursion.
- `longest_excursion_sec`: Longest continuous excursion event duration.
- `max_grade_reached`: Peak excursion grade observed (0, 1, 2, or 3).
- `excursion_count`: Total number of distinct breach events.
- `heat_excursion_count`: Total number of upper breach events.
- `cold_excursion_count`: Total number of lower breach events.

---

## 4. What is `.joblib` and Model Serialization?

### What is `.joblib`?
`joblib` is a specialized Python library optimized for serializing large NumPy arrays and scikit-learn estimators.
- Standard Python `pickle` can be slow and memory-intensive when storing large trees and matrices.
- `joblib.dump(model, 'path.joblib')` compresses the trained decision trees, internal split thresholds, leaf values, and preprocessing state into a single portable binary file.
- `joblib.load('path.joblib')` deserializes the fitted pipeline directly into memory in milliseconds without needing to retrain.

### Stored Artifacts:
- **Model Binary:** `backend/ml/artifacts/viability_model.joblib`
- **Metadata & Report:** `backend/ml/artifacts/model_metadata.json`

---

## 5. Model Training & Evaluation
The offline training pipeline is defined in `backend/ml/train_model.py`:
- Dataset: `backend/ml/cryoursus_compact_excursion_grade_synthetic.csv` (300 records).
- Preprocessing: `ColumnTransformer` with `OneHotEncoder(sparse_output=False)` for categorical features and passthrough for numeric durations.
- Model: `RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)`.

### Validation Performance:
- **Test $R^2$ Score:** `0.9423` (explains >94% of viability variance)
- **Test MAE:** `1.7282%`
- **Test RMSE:** `2.3327%`

---

## 6. How SHAP (Explainable AI) Works
SHAP uses cooperative game theory (Shapley values) to compute the exact contribution of each excursion feature to the prediction:
$$\text{Prediction} = \text{Base Expected Value} + \sum_{i=1}^M \phi_i$$
Where $\phi_i$ represents the positive or negative impact of feature $i$.

In CryoUrsus:
1. `shap.TreeExplainer` inspects the internal decision paths of the trained Random Forest.
2. For each active shipment telemetry summary, SHAP computes local attributions:
   - e.g., `Heat Grade 3 Duration (60s)` contributed `-3.8%` to viability.
   - e.g., `Total Excursion Time (120s)` contributed `-4.5%` to viability.
3. The explanation panel displays these attributions directly on the dashboard.

---

## 7. Operational Lifecycle & Commands

### Train the Model Offline (On-Demand):
```powershell
backend\venv\Scripts\python.exe backend\ml\train_model.py
```

### Run Backend Server (Loads Model into Memory):
```powershell
backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Run Frontend:
```powershell
cd frontend
npm run dev
```

### Run Test Suite:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests
```
