import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# =========================
# DOSSIERS
# =========================
os.makedirs("model", exist_ok=True)

# =========================
# CHARGEMENT DU DATASET
# =========================
DATA_PATH = "data/cultures_agricoles.csv"
MODEL_PATH = "model/model.pkl"
RESULTS_PATH = "model/model_results.csv"

# Vérification de l'existence du fichier avant de charger
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Le fichier {DATA_PATH} est introuvable. Vérifiez le chemin.")

df = pd.read_csv(DATA_PATH)

# =========================
# NETTOYAGE DES DONNÉES
# =========================
df = df.dropna().drop_duplicates()
print(f"Dataset chargé et nettoyé : {df.shape}")

# =========================
# SÉPARATION FEATURES / CIBLE
# =========================
features_list = [
    "region", "culture", "temperature", "temperature_max", 
    "humidite", "pluviometrie", "et0", "stress_hydrique", 
    "ndvi", "ph", "engrais", "irrigation", "ndvi_source", "type_sol"
]

# Conserver uniquement les colonnes du modèle présentes dans le dataset
existing_features = [col for col in features_list if col in df.columns]
X = df[existing_features]
y = df["rendement"]

# Définition des colonnes
categorical_cols = ["region", "culture", "type_sol", "irrigation", "ndvi_source"]
numeric_cols = [
    "temperature", "temperature_max", "humidite", "pluviometrie", 
    "et0", "stress_hydrique", "ndvi", "ph", "engrais"
]

cat_features_in_df = [c for c in categorical_cols if c in X.columns]
num_features_in_df = [c for c in numeric_cols if c in X.columns]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features_in_df),
    ("num", StandardScaler(), num_features_in_df)
])

# =========================
# SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# MODÈLES
# =========================
models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(random_state=42)
}

results = []
best_model = None
best_score = -float("inf")
best_name = ""

print("\n📊 Comparaison des modèles")

for name, algo in models.items():

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", algo)
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)

    print(f"\n{name}")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R²   : {r2:.4f}")

    results.append({
        "modele": name,
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
    })

    if r2 > best_score:
        best_score = r2
        best_model = pipeline
        best_name = name

# =========================
# SAUVEGARDE
# =========================
joblib.dump(best_model, MODEL_PATH)

results_df = pd.DataFrame(results)
results_df.to_csv(RESULTS_PATH, index=False)

print("\n🏆 Meilleur modèle :", best_name)
print("💾 Modèle sauvegardé dans :", MODEL_PATH)
print("💾 Résultats sauvegardés dans :", RESULTS_PATH)