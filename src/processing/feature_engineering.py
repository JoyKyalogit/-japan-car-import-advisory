"""Feature engineering for ML price prediction."""

import pandas as pd

from src.ml.train import FEATURE_COLS, TARGET_COL, prepare_training_data


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features for modeling."""
    featured = df.copy()

    if "year" in featured.columns:
        current_year = pd.Timestamp.now().year
        featured["vehicle_age"] = current_year - featured["year"]

    if "mileage_km" in featured.columns and "year" in featured.columns:
        age = featured.get("vehicle_age", 1).clip(lower=1)
        featured["km_per_year"] = featured["mileage_km"] / age

    if "engine_cc" in featured.columns:
        featured["engine_category"] = pd.cut(
            featured["engine_cc"],
            bins=[0, 1500, 3000, 10000],
            labels=["small", "medium", "large"],
        )

    if "price_jpy" in featured.columns and "mileage_km" in featured.columns:
        featured["price_per_km"] = featured["price_jpy"] / featured["mileage_km"].clip(lower=1)

    return featured


def prepare_ml_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build features and return X, y ready for training."""
    featured = build_features(df)
    prepared = prepare_training_data(featured)
    X = prepared[FEATURE_COLS]
    y = prepared[TARGET_COL]
    return X, y
