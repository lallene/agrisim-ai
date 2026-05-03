"""
Dataset mondial ameliore v3
1. FAOSTAT local CSV (telechargeable sur fao.org/faostat QCL)
   -> fallback World Bank si fichier absent
2. NDVI MODIS (NASA AppEEARS) + fallback simule
3. Stress hydrique (precipitation / ET0)
4. Sol certifie SoilGrids (ISRIC) + fallback aleatoire
5. Nigeria holdout pour test de generalisation geographique
"""

import os
import time
import random
import logging
import requests
import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT_FILE     = "data/cultures_agricoles.csv"
CHECKPOINT_FILE = "data/checkpoint_v3.csv"
LOG_FILE        = "data/generation_v3.log"
FAOSTAT_CSV     = "data/QCL_data.csv"   # telecharger sur fao.org/faostat -> QCL -> Yield
HOLDOUT_COUNTRY = "Nigeria"

YEARS = list(range(2015, 2023))

os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# Codes item FAOSTAT par culture
FAOSTAT_ITEM_CODES = {
    "Ble":              15,
    "Riz (paddy)":      27,
    "Mais":             56,
    "Orge":             44,
    "Sorgho":           83,
    "Millet":           79,
    "Teff":             101,
    "Avoine":           75,
    "Soja":             236,
    "Pomme de terre":   116,
    "Betterave sucriere": 157,
    "Manioc":           125,
    "Canne a sucre":    156,
    "Coton":            328,
    "Tournesol":        267,
    "Arachide":         242,
}

# Mapping noms de cultures (accents -> sans accents) pour FAOSTAT_ITEM_CODES
CULTURE_NORMALIZE = {
    "Bl\u00e9":                    "Ble",
    "Ma\u00efs":                   "Mais",
    "Betterave sucri\u00e8re":     "Betterave sucriere",
    "Canne \u00e0 sucre":          "Canne a sucre",
}

COUNTRIES = {
    "France": {
        "code_fao": "68", "code_iso3": "FRA", "hemisphere": "north",
        "regions": [
            {"region": "Ile-de-France",     "lat": 48.85, "lon": 2.35},
            {"region": "Grand Est",          "lat": 48.58, "lon": 7.75},
            {"region": "Occitanie",          "lat": 43.60, "lon": 1.44},
            {"region": "Bretagne",           "lat": 48.11, "lon": -1.68},
            {"region": "Nouvelle-Aquitaine", "lat": 44.84, "lon": -0.58},
        ],
        "cultures": ["Bl\u00e9", "Ma\u00efs", "Orge", "Avoine", "Soja",
                     "Pomme de terre", "Betterave sucri\u00e8re", "Tournesol"],
    },
    "India": {
        "code_fao": "100", "code_iso3": "IND", "hemisphere": "north",
        "regions": [
            {"region": "Punjab",      "lat": 31.14, "lon": 75.34},
            {"region": "Tamil Nadu",  "lat": 11.12, "lon": 78.65},
            {"region": "West Bengal", "lat": 22.98, "lon": 87.85},
            {"region": "Maharashtra", "lat": 19.08, "lon": 75.73},
            {"region": "Rajasthan",   "lat": 26.92, "lon": 75.79},
        ],
        "cultures": ["Riz (paddy)", "Bl\u00e9", "Ma\u00efs", "Canne \u00e0 sucre", "Coton", "Millet"],
    },
    "USA": {
        "code_fao": "231", "code_iso3": "USA", "hemisphere": "north",
        "regions": [
            {"region": "Midwest",      "lat": 41.88, "lon": -93.10},
            {"region": "California",   "lat": 36.77, "lon": -119.41},
            {"region": "Great Plains", "lat": 39.01, "lon": -98.48},
            {"region": "Southeast",    "lat": 33.75, "lon": -84.39},
        ],
        "cultures": ["Ma\u00efs", "Bl\u00e9", "Soja", "Pomme de terre", "Coton"],
    },
    "Brazil": {
        "code_fao": "21", "code_iso3": "BRA", "hemisphere": "south",
        "regions": [
            {"region": "Sao Paulo",   "lat": -23.55, "lon": -46.63},
            {"region": "Parana",      "lat": -25.25, "lon": -52.02},
            {"region": "Mato Grosso", "lat": -12.64, "lon": -55.42},
            {"region": "Rio Grande",  "lat": -30.03, "lon": -51.22},
        ],
        "cultures": ["Soja", "Ma\u00efs", "Riz (paddy)", "Canne \u00e0 sucre", "Coton"],
    },
    "China": {
        "code_fao": "41", "code_iso3": "CHN", "hemisphere": "north",
        "regions": [
            {"region": "North China Plain",   "lat": 36.50, "lon": 115.00},
            {"region": "Yangtze River Basin", "lat": 30.60, "lon": 114.30},
            {"region": "South China",         "lat": 23.13, "lon": 113.26},
            {"region": "Northeast China",     "lat": 43.89, "lon": 125.33},
        ],
        "cultures": ["Riz (paddy)", "Bl\u00e9", "Ma\u00efs", "Soja", "Coton"],
    },
    "Nigeria": {
        "code_fao": "159", "code_iso3": "NGA", "hemisphere": "north",
        "regions": [
            {"region": "North West",  "lat": 12.00, "lon": 7.60},
            {"region": "South East",  "lat": 6.45,  "lon": 7.50},
            {"region": "Middle Belt", "lat": 8.50,  "lon": 8.50},
        ],
        "cultures": ["Manioc", "Ma\u00efs", "Sorgho", "Millet", "Riz (paddy)", "Arachide"],
    },
    "Australia": {
        "code_fao": "10", "code_iso3": "AUS", "hemisphere": "south",
        "regions": [
            {"region": "New South Wales",   "lat": -33.86, "lon": 151.20},
            {"region": "Queensland",        "lat": -20.91, "lon": 142.70},
            {"region": "Victoria",          "lat": -37.81, "lon": 144.96},
            {"region": "Western Australia", "lat": -31.95, "lon": 115.86},
        ],
        "cultures": ["Bl\u00e9", "Orge", "Avoine", "Sorgho", "Canne \u00e0 sucre"],
    },
    "Ethiopia": {
        "code_fao": "238", "code_iso3": "ETH", "hemisphere": "north",
        "regions": [
            {"region": "Oromia", "lat": 8.50,  "lon": 39.00},
            {"region": "Amhara", "lat": 11.50, "lon": 38.00},
        ],
        "cultures": ["Teff", "Sorgho", "Ma\u00efs", "Bl\u00e9", "Orge"],
    },
    "Ukraine": {
        "code_fao": "230", "code_iso3": "UKR", "hemisphere": "north",
        "regions": [
            {"region": "Kharkiv", "lat": 49.99, "lon": 36.23},
            {"region": "Odessa",  "lat": 46.49, "lon": 30.72},
            {"region": "Poltava", "lat": 49.59, "lon": 34.55},
        ],
        "cultures": ["Bl\u00e9", "Ma\u00efs", "Orge", "Soja", "Tournesol"],
    },
    "Argentina": {
        "code_fao": "9", "code_iso3": "ARG", "hemisphere": "south",
        "regions": [
            {"region": "Pampas",  "lat": -35.00, "lon": -62.00},
            {"region": "Cordoba", "lat": -31.42, "lon": -64.18},
        ],
        "cultures": ["Soja", "Bl\u00e9", "Ma\u00efs", "Sorgho", "Tournesol"],
    },
}

HEMISPHERE_PERIODS = {
    "north": ("04-01", "09-30"),
    "south": ("10-01", "03-31"),
}

_faostat_cache  = {}
_soilgrid_cache = {}
_wb_cache       = {}
_faostat_df     = None


def _normalize_culture(culture):
    return CULTURE_NORMALIZE.get(culture, culture)


# ── FAOSTAT local CSV ────────────────────────────────────────────────────────
def _load_faostat_csv():
    global _faostat_df
    if _faostat_df is not None:
        return True
    if not Path(FAOSTAT_CSV).exists():
        log.warning("QCL_data.csv absent -> World Bank fallback actif")
        log.warning("Pour l'obtenir : fao.org/faostat -> QCL -> Download -> Yield, 2015-2022")
        return False
    log.info("Chargement FAOSTAT local : %s", FAOSTAT_CSV)
    df = pd.read_csv(FAOSTAT_CSV, low_memory=False)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Filtre element Yield (code 5419) ou colonne texte element
    if "element_code" in df.columns:
        df = df[df["element_code"] == 5419]
    elif "element" in df.columns:
        df = df[df["element"].str.lower().str.contains("yield", na=False)]
    _faostat_df = df
    log.info("FAOSTAT charge : %d lignes", len(_faostat_df))
    return True


FAOSTAT_LOCAL = Path("data/faostat_yields.csv")
_faostat_local_df = None

def _load_faostat_local():
    global _faostat_local_df
    if _faostat_local_df is None:
        if not FAOSTAT_LOCAL.exists():
            raise FileNotFoundError(
                f"{FAOSTAT_LOCAL} introuvable — lancez d'abord : python download_faostat.py"
            )
        _faostat_local_df = pd.read_csv(FAOSTAT_LOCAL)
        log.info("FAOSTAT local chargé : %d lignes", len(_faostat_local_df))
    return _faostat_local_df


def get_faostat_yield(country_fao_code, culture, year):
    """Rendement FAOSTAT en t/ha depuis le CSV local, sinon World Bank."""
    culture_key = _normalize_culture(culture)
    item_code   = FAOSTAT_ITEM_CODES.get(culture_key)
    if item_code is None:
        return None

    cache_key = (country_fao_code, item_code, year)
    if cache_key in _faostat_cache:
        return _faostat_cache[cache_key]

    # Lecture CSV local
    if _load_faostat_csv():
        df = _faostat_df
        # Colonnes possibles selon version FAO : area_code, area_code_(fao), item_code, year_code...
        area_col = next((c for c in df.columns if "area_code" in c and "fao" not in c), None)
        item_col = next((c for c in df.columns if c in ("item_code", "item_code_(fao)")), None)
        year_col = next((c for c in df.columns if c in ("year", "year_code")), None)
        val_col  = next((c for c in df.columns if c == "value"), None)

        if all([area_col, item_col, year_col, val_col]):
            mask = (
                (df[area_col].astype(str) == str(country_fao_code)) &
                (df[item_col].astype(str) == str(item_code)) &
                (df[year_col].astype(str) == str(year))
            )
            rows = df[mask]
            if not rows.empty:
                value  = float(rows.iloc[0][val_col])   # hg/ha
                result = round(value / 10_000, 3)        # -> t/ha
                _faostat_cache[cache_key] = result
                log.info("    FAOSTAT CSV pays=%s culture=%s %d -> %.3f t/ha",
                         country_fao_code, culture, year, result)
                return result

    # World Bank fallback
    result = _get_worldbank_yield(country_fao_code, culture, year)
    _faostat_cache[cache_key] = result
    return result


# Facteurs par culture relatifs a la moyenne cereales
_CULTURE_FACTORS = {
    "Ble": 1.00, "Riz (paddy)": 0.95, "Mais": 1.10, "Orge": 0.90,
    "Sorgho": 0.75, "Millet": 0.65, "Teff": 0.55, "Avoine": 0.80,
    "Soja": 0.70, "Pomme de terre": 1.35, "Betterave sucriere": 1.45,
    "Manioc": 1.15, "Canne a sucre": 1.50, "Coton": 0.60,
    "Tournesol": 0.68, "Arachide": 0.72,
}

_FAO_TO_ISO3 = {
    "68": "FRA", "100": "IND", "231": "USA", "21": "BRA",
    "41": "CHN", "159": "NGA", "10":  "AUS", "238": "ETH",
    "230": "UKR", "9":  "ARG",
}


def _get_worldbank_yield(country_fao_code, culture, year):
    iso3   = _FAO_TO_ISO3.get(str(country_fao_code), "WLD")
    wb_key = (iso3, year)

    if wb_key not in _wb_cache:
        url = (
            f"https://api.worldbank.org/v2/country/{iso3}/indicator/"
            f"AG.YLD.CREL.KG?format=json&date={year}"
        )
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data  = r.json()
            value = data[1][0].get("value") if len(data) > 1 and data[1] else None
            _wb_cache[wb_key] = round(float(value) / 1000, 3) if value else None
        except Exception as exc:
            log.warning("    WorldBank echec (%s %d) : %s", iso3, year, exc)
            _wb_cache[wb_key] = None

    base = _wb_cache[wb_key]
    if base is None:
        return None

    culture_key = _normalize_culture(culture)
    factor      = _CULTURE_FACTORS.get(culture_key, 1.0)
    result      = round(base * factor, 3)
    log.info("    WorldBank fallback %s culture=%s %d -> %.3f t/ha", iso3, culture, year, result)
    return result


# ── Retry ────────────────────────────────────────────────────────────────────
def with_retry(fn, max_attempts=4, base_delay=1.0):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            log.warning("    Tentative %d/%d echouee (%s) -> attente %.1fs",
                        attempt, max_attempts, exc, delay)
            time.sleep(delay)


# ── Meteo Open-Meteo ─────────────────────────────────────────────────────────
def get_weather_period(lat, lon, year, hemisphere="north"):
    start_md, end_md = HEMISPHERE_PERIODS[hemisphere]
    if hemisphere == "south":
        start_date, end_date = f"{year}-{start_md}", f"{year+1}-{end_md}"
    else:
        start_date, end_date = f"{year}-{start_md}", f"{year}-{end_md}"

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_mean,temperature_2m_max,relative_humidity_2m_mean,"
        "precipitation_sum,et0_fao_evapotranspiration"
        "&timezone=auto"
    )

    def _fetch():
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r

    resp  = with_retry(_fetch)
    daily = resp.json()["daily"]
    df    = pd.DataFrame(daily)

    temp    = df["temperature_2m_mean"].dropna()
    temp_mx = df["temperature_2m_max"].dropna()
    hum     = df["relative_humidity_2m_mean"].dropna()
    pluv    = df["precipitation_sum"].dropna()
    et0     = df["et0_fao_evapotranspiration"].dropna()

    if len(temp) == 0:
        raise ValueError("Donnees meteo vides")

    et0_sum  = float(et0.sum())
    pluv_sum = float(pluv.sum())
    stress   = round(min(pluv_sum / et0_sum, 1.0), 3) if et0_sum > 0 else 0.5

    return {
        "date_debut":      start_date,
        "date_fin":        end_date,
        "temperature":     round(float(temp.mean()), 2),
        "temperature_max": round(float(temp_mx.mean()), 2),
        "humidite":        round(float(hum.mean()), 2) if len(hum) > 0 else None,
        "pluviometrie":    round(pluv_sum, 2),
        "et0":             round(et0_sum, 2),
        "stress_hydrique": stress,
    }


# ── NDVI ─────────────────────────────────────────────────────────────────────
MODIS_TOKEN = os.getenv("NASA_EARTHDATA_TOKEN", "")


def get_ndvi_modis(lat, lon, year, hemisphere="north"):
    if not MODIS_TOKEN:
        raise EnvironmentError("NASA_EARTHDATA_TOKEN non defini")
    start_md, end_md = HEMISPHERE_PERIODS[hemisphere]
    start_date = f"{year}-{start_md}"
    end_date   = f"{year+1}-{end_md}" if hemisphere == "south" else f"{year}-{end_md}"

    headers = {"Authorization": f"Bearer {MODIS_TOKEN}"}
    payload = {
        "task_name": f"ndvi_{lat}_{lon}_{year}",
        "task_type": "point",
        "start_date": start_date,
        "end_date":   end_date,
        "layers":     [{"product": "MOD13Q1.061", "layer": "_250m_16_days_NDVI"}],
        "coordinates":[{"latitude": lat, "longitude": lon, "id": "pt1", "category": "site"}],
        "output":     {"format": {"type": "geotiff"}, "projection": "geographic"},
    }
    submit = requests.post(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        json=payload, headers=headers, timeout=30
    )
    submit.raise_for_status()
    task_id = submit.json()["task_id"]

    for _ in range(36):
        time.sleep(5)
        status = requests.get(
            f"https://appeears.earthdatacloud.nasa.gov/api/task/{task_id}",
            headers=headers, timeout=15
        )
        if status.json().get("status") == "done":
            break
    else:
        raise TimeoutError("AppEEARS timeout")

    files    = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}",
        headers=headers, timeout=15
    ).json()["files"]
    csv_file = next(f for f in files if f["file_name"].endswith(".csv"))
    from io import StringIO
    dl = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}/{csv_file['file_id']}",
        headers=headers, stream=True, timeout=60
    )
    df_ndvi   = pd.read_csv(StringIO(dl.text))
    col       = [c for c in df_ndvi.columns if "NDVI" in c][0]
    ndvi_vals = pd.to_numeric(df_ndvi[col], errors="coerce").dropna()
    ndvi_vals = ndvi_vals[(ndvi_vals > -2000) & (ndvi_vals <= 10000)]
    if len(ndvi_vals) == 0:
        raise ValueError("Aucune valeur NDVI valide")
    return round(float((ndvi_vals * 0.0001).mean()), 4)


def ndvi_simulated(lat, lon, year, temperature, pluviometrie, culture):
    rng = random.Random(hash((lat, lon, year, culture)) & 0x7FFFFFFF)
    if pluviometrie < 200:
        base = 0.20
    elif pluviometrie < 500:
        base = 0.40
    elif pluviometrie < 900:
        base = 0.60
    else:
        base = 0.72

    if temperature < 5 or temperature > 36:
        base -= 0.15
    elif 15 <= temperature <= 28:
        base += 0.05

    bonus = {
        "Ma\u00efs": 0.08, "Canne \u00e0 sucre": 0.10, "Manioc": 0.06,
        "Riz (paddy)": 0.05, "Soja": 0.04, "Bl\u00e9": 0.02,
        "Millet": -0.02, "Sorgho": 0.01, "Teff": -0.01,
    }
    base += bonus.get(culture, 0.0)
    return round(min(max(base + rng.uniform(-0.05, 0.05), 0.05), 0.95), 4)


def get_ndvi(lat, lon, year, hemisphere, temperature, pluviometrie, culture):
    try:
        ndvi   = get_ndvi_modis(lat, lon, year, hemisphere)
        source = "MODIS"
    except Exception as exc:
        log.info("    NDVI MODIS indisponible (%s) -> fallback simule", exc)
        ndvi   = ndvi_simulated(lat, lon, year, temperature, pluviometrie, culture)
        source = "simulated"
    return ndvi, source


# ── SoilGrids ────────────────────────────────────────────────────────────────
def get_soil_type_soilgrids(lat, lon):
    cache_key = (round(lat, 1), round(lon, 1))
    if cache_key in _soilgrid_cache:
        return _soilgrid_cache[cache_key]

    url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lon={lon}&lat={lat}&property=sand&property=clay&depth=0-30cm&value=mean"
    )
    try:
        def _fetch():
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        data   = with_retry(_fetch, max_attempts=2)
        layers = data["properties"]["layers"]
        sand   = next(l for l in layers if l["name"] == "sand")
        clay   = next(l for l in layers if l["name"] == "clay")
        sp     = sand["depths"][0]["values"]["mean"] / 10
        cp     = clay["depths"][0]["values"]["mean"] / 10
        if sp > 70:
            soil = "sableux"
        elif cp > 40:
            soil = "argileux"
        elif cp > 20 and sp < 50:
            soil = "argilo-limoneux"
        else:
            soil = "limoneux"
    except Exception as exc:
        log.info("    SoilGrids indisponible (%s) -> aleatoire", exc)
        soil = random.choice(["limoneux", "argileux", "sableux", "argilo-limoneux"])

    _soilgrid_cache[cache_key] = soil
    return soil


# ── Ajustement rendement ─────────────────────────────────────────────────────
SOIL_FACTORS = {
    "limoneux": 1.05, "argileux": 0.98,
    "sableux":  0.90, "argilo-limoneux": 1.02,
}


def adjust_yield(base, temperature, stress_hydrique, ndvi,
                 type_sol, ph, engrais, irrigation):
    r = base
    r *= SOIL_FACTORS.get(type_sol, 1.0)
    r *= 1.08 if irrigation == "oui" else 0.92

    if engrais >= 120:   r *= 1.10
    elif engrais >= 90:  r *= 1.05
    elif engrais < 60:   r *= 0.88

    r *= 1.04 if 6.2 <= ph <= 7.2 else 0.93

    if temperature > 34:    r *= 0.82
    elif temperature > 30:  r *= 0.90
    elif temperature < 5:   r *= 0.80
    elif temperature < 10:  r *= 0.90

    if stress_hydrique < 0.3:    r *= 0.75
    elif stress_hydrique < 0.6:  r *= 0.90
    elif stress_hydrique > 0.95: r *= 0.96

    if ndvi < 0.2:     r *= 0.80
    elif ndvi < 0.4:   r *= 0.92
    elif ndvi >= 0.7:  r *= 1.08

    r *= random.uniform(0.95, 1.05)
    return round(max(r, 0.1), 3)


# ── Checkpoint ───────────────────────────────────────────────────────────────
def load_checkpoint():
    if Path(CHECKPOINT_FILE).exists():
        df   = pd.read_csv(CHECKPOINT_FILE)
        done = set(zip(df["pays"], df["region"], df["annee"].astype(str), df["culture"]))
        log.info("Checkpoint : %d lignes, %d combos deja traites", len(df), len(done))
        return df.to_dict("records"), done
    return [], set()


def save_checkpoint(rows):
    pd.DataFrame(rows).to_csv(CHECKPOINT_FILE, index=False)


# ── Generation principale ────────────────────────────────────────────────────
def generate_dataset():
    random.seed(42)
    rows, done = load_checkpoint()

    engrais_values    = [50, 70, 90, 110, 130]
    irrigation_values = ["oui", "non"]

    for country_name, cdata in COUNTRIES.items():
        is_holdout = (country_name == HOLDOUT_COUNTRY)
        log.info("Pays : %s%s", country_name,
                 " [HOLDOUT]" if is_holdout else "")

        for rdata in cdata["regions"]:
            region, lat, lon = rdata["region"], rdata["lat"], rdata["lon"]
            hemisphere       = cdata.get("hemisphere", "north")
            log.info("  Region : %s", region)

            soil_certified = get_soil_type_soilgrids(lat, lon)
            log.info("    Sol SoilGrids : %s", soil_certified)

            for year in YEARS:
                try:
                    weather = get_weather_period(lat, lon, year, hemisphere)
                except Exception as exc:
                    log.error("    %d meteo : %s", year, exc)
                    continue

                for culture in cdata["cultures"]:
                    key = (country_name, region, str(year), culture)
                    if key in done:
                        continue

                    base_yield = get_faostat_yield(cdata["code_fao"], culture, year)
                    if base_yield is None:
                        log.warning("    %d %s -> rendement indisponible", year, culture)
                        continue

                    ndvi, ndvi_src = get_ndvi(
                        lat, lon, year, hemisphere,
                        weather["temperature"], weather["pluviometrie"], culture
                    )

                    for engrais in engrais_values:
                        for irrigation in irrigation_values:
                            ph = round(random.uniform(5.7, 7.6), 2)
                            rendement = adjust_yield(
                                base_yield,
                                weather["temperature"],
                                weather["stress_hydrique"],
                                ndvi,
                                soil_certified,
                                ph, engrais, irrigation,
                            )
                            rows.append({
                                "pays":            country_name,
                                "region":          region,
                                "annee":           year,
                                "date_debut":      weather["date_debut"],
                                "date_fin":        weather["date_fin"],
                                "latitude":        lat,
                                "longitude":       lon,
                                "culture":         culture,
                                "temperature":     weather["temperature"],
                                "temperature_max": weather["temperature_max"],
                                "humidite":        weather["humidite"],
                                "pluviometrie":    weather["pluviometrie"],
                                "et0":             weather["et0"],
                                "stress_hydrique": weather["stress_hydrique"],
                                "ndvi":            ndvi,
                                "ndvi_source":     ndvi_src,
                                "type_sol":        soil_certified,
                                "ph":              ph,
                                "engrais":         engrais,
                                "irrigation":      irrigation,
                                "rendement":       rendement,
                                "holdout":         is_holdout,
                            })

                    done.add(key)
                    save_checkpoint(rows)
                    log.info("    %d %s (NDVI=%.3f [%s], sol=%s, stress=%.2f) -> OK",
                             year, culture, ndvi, ndvi_src,
                             soil_certified, weather["stress_hydrique"])
                    time.sleep(0.3)

    df = pd.DataFrame(rows)
    if df.empty:
        log.error("Aucune donnee generee.")
        return

    df.to_csv(OUTPUT_FILE, index=False)
    if Path(CHECKPOINT_FILE).exists():
        Path(CHECKPOINT_FILE).unlink()

    train_df   = df[df["holdout"] == False]
    holdout_df = df[df["holdout"] == True]

    log.info("Dataset v3 genere : %s", OUTPUT_FILE)
    log.info("  Total   : %d lignes", len(df))
    log.info("  Train   : %d lignes (%d pays)", len(train_df), train_df["pays"].nunique())
    log.info("  Holdout : %d lignes (%s)", len(holdout_df), HOLDOUT_COUNTRY)
    log.info("  NDVI sources : %s", df["ndvi_source"].value_counts().to_dict())


if __name__ == "__main__":
    generate_dataset()