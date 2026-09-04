"""Train XGBoost model to predict car prices in Japan."""

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from src.config import settings

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "make",
    "model",
    "year",
    "mileage_km",
    "engine_cc",
    "fuel_type",
    "transmission",
    "body_type",
    "source_platform",
]
TARGET_COL = "price_jpy"
CATEGORICAL = ["make", "model", "fuel_type", "transmission", "body_type", "source_platform"]
NUMERIC = ["year", "mileage_km", "engine_cc"]


def prepare_training_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for col in FEATURE_COLS + [TARGET_COL]:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")

    data = data.dropna(subset=[TARGET_COL, "year", "mileage_km", "engine_cc"])
    data = data[data[TARGET_COL] > 0]

    for col in CATEGORICAL:
        data[col] = data[col].fillna("Unknown").astype(str)

    for col in NUMERIC:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=NUMERIC)

    return data


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", "passthrough", NUMERIC),
        ]
    )
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def train_model(df: pd.DataFrame, test_size: float = 0.2) -> dict:
    data = prepare_training_data(df)
    X = data[FEATURE_COLS]
    y = data[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = {
        "r2": round(r2_score(y_test, y_pred), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
        "mae": round(mean_absolute_error(y_test, y_pred), 2),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    model_path = Path(settings.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "feature_cols": FEATURE_COLS, "metrics": metrics}, model_path)

    logger.info("Model saved to %s | R²=%.4f RMSE=%.0f", model_path, metrics["r2"], metrics["rmse"])
    return metrics
