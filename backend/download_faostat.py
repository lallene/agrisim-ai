"""
download_faostat.py
───────────────────
Télécharge le fichier bulk FAOSTAT (Production_Crops_Livestock_E_All_Data.zip)
directement depuis fao.org, l'extrait et construit une table de rendements
par pays / culture / année prête à l'emploi.

Usage :
    python download_faostat.py

Sortie :
    ../data/faostat_yields.csv   ← table filtrée (pays, culture, année, rendement t/ha)
    ../data/faostat_raw/         ← fichiers CSV bruts extraits du zip
"""

import io
import os
import zipfile
import requests
import pandas as pd
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
FAOSTAT_ZIP_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
)
RAW_DIR    = Path("data/faostat_raw")
OUTPUT_CSV = Path("data/faostat_yields.csv")

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── Pays retenus (nom FAOSTAT exact) ─────────────────────────────────────────
COUNTRIES_FAO = [
    "France", "India", "United States of America", "Brazil", "China, mainland",
    "Nigeria", "Australia", "Ethiopia", "Ukraine", "Argentina",
]

# ── Cultures retenues ─────────────────────────────────────────────────────────
CULTURES_FAO = [
    "Wheat", "Rice, paddy", "Maize (corn)", "Barley", "Sorghum", "Millet",
    "Teff", "Oats", "Soybeans", "Potatoes", "Sugar beet", "Cassava",
    "Sugar cane", "Seed cotton, unginned", "Sunflower seed", "Groundnuts, excluding shelled",
]

# Correspondance nom FAOSTAT → nom utilisé dans le projet
CULTURE_RENAME = {
    "Wheat":                          "Blé",
    "Rice, paddy":                    "Riz (paddy)",
    "Maize (corn)":                   "Maïs",
    "Barley":                         "Orge",
    "Sorghum":                        "Sorgho",
    "Millet":                         "Millet",
    "Teff":                           "Teff",
    "Oats":                           "Avoine",
    "Soybeans":                       "Soja",
    "Potatoes":                       "Pomme de terre",
    "Sugar beet":                     "Betterave sucrière",
    "Cassava":                        "Manioc",
    "Sugar cane":                     "Canne à sucre",
    "Seed cotton, unginned":          "Coton",
    "Sunflower seed":                 "Tournesol",
    "Groundnuts, excluding shelled":  "Arachide",
}

YEARS = list(range(2015, 2023))


def download_zip():
    zip_path = RAW_DIR / "faostat_crops.zip"

    if zip_path.exists():
        print(f"✓ Zip déjà téléchargé : {zip_path}")
        return zip_path

    print(f"⬇ Téléchargement FAOSTAT bulk CSV (~150 Mo)...")
    print(f"  URL : {FAOSTAT_ZIP_URL}")

    response = requests.get(FAOSTAT_ZIP_URL, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {pct:.1f}%  ({downloaded/1e6:.1f} Mo)", end="", flush=True)

    print(f"\n✓ Téléchargé : {zip_path}  ({downloaded/1e6:.1f} Mo)")
    return zip_path


def extract_zip(zip_path):
    print(f"\n📦 Extraction...")
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        print(f"  Fichiers dans le zip : {names}")

        # Le fichier normalisé s'appelle généralement *_NOFLAG.csv ou *Normalized*.csv
        target = next(
            (n for n in names if n.endswith(".csv") and "Normalized" in n),
            next((n for n in names if n.endswith(".csv")), None)
        )
        if target is None:
            raise FileNotFoundError("Aucun CSV trouvé dans le zip FAOSTAT")

        csv_path = RAW_DIR / Path(target).name
        if csv_path.exists():
            print(f"  ✓ Déjà extrait : {csv_path}")
        else:
            z.extract(target, RAW_DIR)
            # Renommer si extrait dans un sous-dossier
            extracted = RAW_DIR / target
            if extracted != csv_path:
                extracted.rename(csv_path)
            print(f"  ✓ Extrait : {csv_path}")

    return csv_path


def build_yield_table(csv_path):
    print(f"\n🔍 Chargement du CSV brut (peut prendre 20-30s)...")

    df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
    print(f"  Dimensions brutes : {df.shape}")
    print(f"  Colonnes : {list(df.columns)}")

    # ── Filtre sur l'élément "Yield" (code 5419) ──────────────────────────
    # Les colonnes varient selon la version ; on détecte dynamiquement
    element_col = next((c for c in df.columns if "Element" in c and "Code" not in c), None)
    item_col    = next((c for c in df.columns if "Item" in c and "Code" not in c), None)
    area_col    = next((c for c in df.columns if "Area" in c and "Code" not in c), None)
    year_col    = next((c for c in df.columns if c in ("Year", "year")), None)
    value_col   = next((c for c in df.columns if c in ("Value", "value")), None)

    print(f"\n  Colonnes détectées :")
    print(f"    Area={area_col}, Item={item_col}, Element={element_col}")
    print(f"    Year={year_col}, Value={value_col}")

    if None in (element_col, item_col, area_col, year_col, value_col):
        raise ValueError("Structure CSV FAOSTAT non reconnue — vérifiez le fichier brut")

    # Filtre : Yield uniquement
    df = df[df[element_col] == "Yield"].copy()
    print(f"  Après filtre 'Yield' : {len(df)} lignes")

    # Filtre pays
    df = df[df[area_col].isin(COUNTRIES_FAO)].copy()
    print(f"  Après filtre pays   : {len(df)} lignes")

    # Filtre cultures
    df = df[df[item_col].isin(CULTURES_FAO)].copy()
    print(f"  Après filtre cultures : {len(df)} lignes")

    # Filtre années
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df[df[year_col].isin(YEARS)].copy()
    print(f"  Après filtre années  : {len(df)} lignes")

    # Conversion hg/ha → t/ha
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[value_col])
    df["rendement_tha"] = (df[value_col] / 10_000).round(3)

    # Renommage colonnes
    df = df.rename(columns={
        area_col:    "pays_fao",
        item_col:    "culture_fao",
        year_col:    "annee",
        value_col:   "rendement_hgha",
    })

    # Nom culture → nom projet
    df["culture"] = df["culture_fao"].map(CULTURE_RENAME)

    # Nom pays FAOSTAT → nom projet
    pays_rename = {
        "United States of America": "USA",
        "China, mainland":          "China",
    }
    df["pays"] = df["pays_fao"].replace(pays_rename)

    result = df[["pays", "culture", "annee", "rendement_tha"]].copy()
    result = result.sort_values(["pays", "culture", "annee"]).reset_index(drop=True)

    result.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Table de rendements sauvegardée : {OUTPUT_CSV}")
    print(f"   {len(result)} lignes  |  {result['pays'].nunique()} pays  |  {result['culture'].nunique()} cultures")
    print(f"\n{result.head(12).to_string(index=False)}")
    return result


def main():
    zip_path = download_zip()
    csv_path = extract_zip(zip_path)
    build_yield_table(csv_path)

    print(f"""
─────────────────────────────────────────────────────────
Étape suivante :
  Le fichier ../data/faostat_yields.csv est prêt.
  Lancez ensuite : python generate_cultures_v3.py
  Le script chargera ce fichier au lieu d'appeler l'API.
─────────────────────────────────────────────────────────
""")


if __name__ == "__main__":
    main()
