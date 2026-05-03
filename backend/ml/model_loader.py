import os
from functools import lru_cache

import gdown
import joblib
import numpy as np
import pandas as pd


MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.pkl")

MODEL_ID = os.getenv("MODEL_ID")
METADATA_ID = os.getenv("METADATA_ID")

MIN_MODEL_SIZE = 1_000_000
MIN_METADATA_SIZE = 1_000


def download_file_if_missing(file_id: str | None, output_path: str, label: str, min_size: int):
    if os.path.exists(output_path) and os.path.getsize(output_path) >= min_size:
        print(f"{label} déjà présent ✅")
        return

    if not file_id:
        raise RuntimeError(f"{label} manquant. Ajoute la variable d'environnement correspondante.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    url = f"https://drive.google.com/uc?id={file_id}"

    print(f"Téléchargement {label} depuis Google Drive...")
    gdown.download(url, output_path, quiet=False)

    if not os.path.exists(output_path):
        raise RuntimeError(f"Échec du téléchargement : {label}")

    if os.path.getsize(output_path) < min_size:
        raise RuntimeError(f"{label} corrompu ou incomplet.")


@lru_cache(maxsize=1)
def load_artifacts():
    print("Chargement des artefacts ML...")

    download_file_if_missing(
        MODEL_ID,
        MODEL_PATH,
        "MODEL_ID",
        MIN_MODEL_SIZE
    )

    download_file_if_missing(
        METADATA_ID,
        METADATA_PATH,
        "METADATA_ID",
        MIN_METADATA_SIZE
    )

    model = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)

    print("Modèle chargé avec succès ✅")

    return model, metadata


def prepare_input(data: dict):
    _, metadata = load_artifacts()

    df = pd.DataFrame([data])

    if "stress_hydrique" not in df.columns:
        df["stress_hydrique"] = df["pluviometrie"] / (df["temperature"] + 1)

    if "temperature_max" not in df.columns:
        df["temperature_max"] = df["temperature"] + 5

    if "et0" not in df.columns:
        df["et0"] = df["temperature"] * 0.18

    if "ndvi" not in df.columns:
        df["ndvi"] = 0.55

    if "ndvi_source" not in df.columns:
        df["ndvi_source"] = "simulated"

    missing_cols = [
        col for col in metadata["feature_cols"]
        if col not in df.columns
    ]

    if missing_cols:
        raise ValueError(f"Colonnes manquantes pour le modèle : {missing_cols}")

    return df[metadata["feature_cols"]]


def predict_yield(data: dict):
    model, _ = load_artifacts()

    df = prepare_input(data)

    pred_log = model.predict(df)[0]
    pred_real = np.expm1(pred_log)

    rendement = max(0, float(pred_real))

    return round(rendement, 2)