"""
Train V5 propre
- Pas de variable pays pour meilleure généralisation
- Target transformée en log1p pour éviter les rendements négatifs
- Features agronomiques : stress hydrique, NDVI, ET0
- Sauvegarde du modèle + résultats
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


DATA_PATH = "data/cultures_agricoles.csv"

MODEL_PATH = "model/model.pkl"
RESULTS_PATH = "model/model_results.csv"
METADATA_PATH = "model/model_metadata.pkl"

os.makedirs("model", exist_ok=True)


df = pd.read_csv(DATA_PATH).dropna(subset=["rendement"]).drop_duplicates()

print("Dataset chargé :", df.shape)

if "ndvi_source" not in df.columns:
    df["ndvi_source"] = "simulated"

if "stress_hydrique" not in df.columns:
    df["stress_hydrique"] = df["pluviometrie"] / (df["temperature"] + 1)

if "temperature_max" not in df.columns:
    df["temperature_max"] = df["temperature"] + 5

if "et0" not in df.columns:
    df["et0"] = df["temperature"] * 0.18


# Sécurité : aucun rendement négatif ou nul
df = df[df["rendement"] > 0].copy()

# Target transformée
df["rendement_log"] = np.log1p(df["rendement"])


categorical_cols = [
    "region",
    "culture",
    "type_sol",
    "irrigation",
    "ndvi_source"
]

numeric_cols = [
    "temperature",
    "temperature_max",
    "humidite",
    "pluviometrie",
    "stress_hydrique",
    "et0",
    "ndvi",
    "ph",
    "engrais"
]

feature_cols = categorical_cols + numeric_cols

X = df[feature_cols]
y = df["rendement_log"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ("num", StandardScaler(), numeric_cols)
])

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        random_state=42
    )
}

results = []
best_model = None
best_score = -float("inf")
best_name = ""

print("\nComparaison des modèles V5 :")

for name, model in models.items():
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    pipeline.fit(X_train, y_train)

    y_pred_log = pipeline.predict(X_test)

    # Retour en rendement réel
    y_test_real = np.expm1(y_test)
    y_pred_real = np.expm1(y_pred_log)

    # Sécurité anti-négatif
    y_pred_real = np.maximum(y_pred_real, 0)

    mae = mean_absolute_error(y_test_real, y_pred_real)
    rmse = mean_squared_error(y_test_real, y_pred_real) ** 0.5
    r2 = r2_score(y_test_real, y_pred_real)

    print(f"\n{name}")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R²   : {r2:.4f}")

    results.append({
        "modele": name,
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4)
    })

    if r2 > best_score:
        best_score = r2
        best_model = pipeline
        best_name = name


joblib.dump(best_model, MODEL_PATH)

metadata = {
    "model_type": best_name,
    "target_transform": "log1p",
    "categorical_cols": categorical_cols,
    "numeric_cols": numeric_cols,
    "feature_cols": feature_cols,
    "min_prediction": 0
}

joblib.dump(metadata, METADATA_PATH)

pd.DataFrame(results).to_csv(RESULTS_PATH, index=False)

print("\nMeilleur modèle :", best_name)
print("R² :", round(best_score, 4))
print("Modèle sauvegardé :", MODEL_PATH)
print("Metadata :", METADATA_PATH)
print("Résultats :", RESULTS_PATH)