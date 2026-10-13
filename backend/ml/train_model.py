#!/usr/bin/env python
"""
CryoUrsus Offline Viability Model Training Script.

Trains a scikit-learn RandomForestRegressor to predict remaining product viability (viability_pct)
from excursion-grade durations (in seconds), excursion event counts, and biological type.

The trained pipeline is serialized to backend/ml/artifacts/viability_model.joblib along with
model metadata and performance metrics. It is run offline on-demand and NEVER automatically
during application runtime or simulation ticks.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cryoursus.train")

# Default paths
BASE_ML_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_ML_DIR / "cryoursus_compact_excursion_grade_synthetic.csv"
DEFAULT_ARTIFACT_DIR = BASE_ML_DIR / "artifacts"
MODEL_FILENAME = "viability_model.joblib"
METADATA_FILENAME = "model_metadata.json"

CATEGORICAL_FEATURES = ["biological_type"]
NUMERIC_FEATURES = [
    "heat_grade_1_time_sec",
    "heat_grade_2_time_sec",
    "heat_grade_3_time_sec",
    "cold_grade_1_time_sec",
    "cold_grade_2_time_sec",
    "cold_grade_3_time_sec",
    "grade_1_time_sec",
    "grade_2_time_sec",
    "grade_3_time_sec",
    "excursion_count",
    "heat_excursion_count",
    "cold_excursion_count",
    "total_excursion_time_sec",
    "longest_excursion_sec",
    "max_grade_reached",
]
TARGET_COL = "viability_pct"


def load_and_validate_dataset(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Training dataset not found at: {csv_path}")

    logger.info("Loading dataset from: %s", csv_path)
    df = pd.read_csv(csv_path)

    required_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES + [TARGET_COL]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    # Drop any null target rows
    df = df.dropna(subset=[TARGET_COL])
    logger.info("Dataset loaded successfully: %d rows, %d columns.", len(df), len(df.columns))
    return df


def build_pipeline(random_state: int = 42) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            (
                "num",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=random_state,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )
    return pipeline


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4)}


def train(data_path: Path, artifact_dir: Path, test_size: float = 0.2, random_state: int = 42):
    df = load_and_validate_dataset(data_path)

    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=df["biological_type"]
    )

    logger.info("Training set: %d samples, Test set: %d samples.", len(X_train), len(X_test))

    pipeline = build_pipeline(random_state=random_state)
    logger.info("Fitting RandomForestRegressor pipeline...")
    pipeline.fit(X_train, y_train)

    # Evaluate
    train_preds = pipeline.predict(X_train)
    test_preds = pipeline.predict(X_test)

    train_metrics = evaluate_model(y_train.to_numpy(), train_preds)
    test_metrics = evaluate_model(y_test.to_numpy(), test_preds)

    logger.info("Train Metrics: MAE=%.4f, RMSE=%.4f, R2=%.4f", train_metrics["mae"], train_metrics["rmse"], train_metrics["r2"])
    logger.info("Test Metrics:  MAE=%.4f, RMSE=%.4f, R2=%.4f", test_metrics["mae"], test_metrics["rmse"], test_metrics["r2"])

    # Feature names out of preprocessor
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed_feature_names = list(preprocessor.get_feature_names_out())

    # Create output directory
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / MODEL_FILENAME
    metadata_path = artifact_dir / METADATA_FILENAME

    logger.info("Saving trained pipeline to: %s", model_path)
    joblib.dump(pipeline, model_path)

    metadata = {
        "model_name": "CryoUrsus_Viability_RandomForest",
        "version": "1.0.0",
        "algorithm": "RandomForestRegressor",
        "target": TARGET_COL,
        "input_features": {
            "categorical": CATEGORICAL_FEATURES,
            "numeric": NUMERIC_FEATURES,
        },
        "transformed_feature_names": transformed_feature_names,
        "metrics": {
            "train": train_metrics,
            "test": test_metrics,
        },
        "sample_count": len(df),
        "disclaimer": "Synthetic simulation estimate, not a validated biological stability assessment.",
    }

    logger.info("Saving metadata to: %s", metadata_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Model training and packaging completed successfully!")
    return model_path, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CryoUrsus Viability ML Model")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to synthetic CSV dataset")
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACT_DIR, help="Path to save model artifacts")
    args = parser.parse_args()

    train(args.data, args.artifacts)
