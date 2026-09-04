"""Predict car prices using trained model."""

from pathlib import Path

import joblib
import pandas as pd

from src.config import settings
from src.utils.helpers import jpy_to_usd


def load_model():
    path = Path(settings.model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run: uv run python scripts/train_model.py"
        )
    return joblib.load(path)


def predict_price(
    make: str,
    model: str,
    year: int,
    mileage_km: int,
    engine_cc: int,
    fuel_type: str = "Petrol",
    transmission: str = "Automatic",
    body_type: str = "Sedan",
    source_platform: str = "SBT Japan",
) -> dict:
    artifact = load_model()
    pipeline = artifact["pipeline"]

    input_df = pd.DataFrame(
        [
            {
                "make": make,
                "model": model,
                "year": year,
                "mileage_km": mileage_km,
                "engine_cc": engine_cc,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "body_type": body_type,
                "source_platform": source_platform,
            }
        ]
    )

    price_jpy = float(pipeline.predict(input_df)[0])
    return {
        "price_jpy": round(price_jpy, 0),
        "price_usd": jpy_to_usd(price_jpy),
        "metrics": artifact.get("metrics", {}),
    }
