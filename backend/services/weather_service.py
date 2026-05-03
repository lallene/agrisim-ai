import requests
import pandas as pd
import numpy as np
import time
from datetime import date, timedelta

# ============================================================
# 🔐 SAFE REQUEST (ANTI-CRASH API)
# ============================================================

def safe_request(url, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception:
            if attempt == retries - 1:
                raise ValueError("API météo indisponible")
            time.sleep(1)

# ============================================================
# 🔍 RECHERCHE DE VILLE
# ============================================================

def search_cities(query: str):
    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={query}&count=10&language=fr&format=json"
    )

    response = safe_request(url)
    data = response.json()

    if "results" not in data:
        return []

    return [
        {
            "name": city.get("name"),
            "country": city.get("country"),
            "admin1": city.get("admin1", ""),
            "latitude": city.get("latitude"),
            "longitude": city.get("longitude"),
        }
        for city in data["results"]
    ]

# ============================================================
# 🌦️ FEATURE ENGINEERING MÉTÉO (V6 PRO)
# ============================================================

def build_weather_result(df: pd.DataFrame, source: str):
    if df.empty:
        raise ValueError("Aucune donnée météo disponible.")

    # ── Moyennes réelles ───────────────────────────────
    temperature = float(df["temperature_2m_mean"].mean())
    humidite = float(df["relative_humidity_2m_mean"].mean())
    pluviometrie = float(df["precipitation_sum"].sum())

    # ── Nettoyage intelligent ─────────────────────────
    if np.isnan(pluviometrie) or pluviometrie < 1:
        pluviometrie = 1.0

    if np.isnan(humidite) or humidite < 20:
        humidite = 50.0

    # ── Features avancées ─────────────────────────────
    temperature_max = temperature + 4.5

    # 🌡️ Evapotranspiration (V6 améliorée)
    et0 = 0.408 * temperature + 0.15 * (100 - humidite)

    # 💧 Stress hydrique réaliste
    stress_hydrique = pluviometrie / max(et0, 1)

    # 🌿 NDVI dynamique (corrélé climat)
    ndvi = 0.3 + (pluviometrie / 2000) + (humidite / 200)
    ndvi = max(0.2, min(ndvi, 0.85))

    return {
        "temperature": round(temperature, 2),
        "temperature_max": round(temperature_max, 2),
        "humidite": round(humidite, 2),
        "pluviometrie": round(pluviometrie, 2),
        "stress_hydrique": round(stress_hydrique, 3),
        "et0": round(et0, 2),
        "ndvi": round(ndvi, 2),
        "source_meteo": source
    }

# ============================================================
# 📊 HISTORIQUE
# ============================================================

def get_weather_archive(latitude, longitude, date_debut, date_fin):
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={latitude}&longitude={longitude}"
        f"&start_date={date_debut}&end_date={date_fin}"
        "&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum"
        "&timezone=auto"
    )

    response = safe_request(url)
    df = pd.DataFrame(response.json()["daily"])

    return build_weather_result(df, "historique")

# ============================================================
# 🔮 PRÉVISION
# ============================================================

def get_weather_forecast(latitude, longitude, date_debut, date_fin):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&start_date={date_debut}&end_date={date_fin}"
        "&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum"
        "&timezone=auto"
    )

    response = safe_request(url)
    df = pd.DataFrame(response.json()["daily"])

    return build_weather_result(df, "prévision")

# ============================================================
# 🌍 MOYENNE CLIMATIQUE
# ============================================================

def get_weather_climate_average(latitude, longitude, date_debut, date_fin):
    years = range(2016, 2023)
    all_rows = []

    for year in years:
        start = date(year, date_debut.month, date_debut.day)
        end = date(year, date_fin.month, date_fin.day)

        if end < start:
            end = date(year + 1, date_fin.month, date_fin.day)

        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={latitude}&longitude={longitude}"
            f"&start_date={start}&end_date={end}"
            "&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum"
            "&timezone=auto"
        )

        try:
            response = safe_request(url)
            df = pd.DataFrame(response.json()["daily"])

            if not df.empty:
                all_rows.append(df)

        except Exception:
            continue

    if not all_rows:
        raise ValueError("Impossible de calculer la moyenne climatique.")

    final_df = pd.concat(all_rows, ignore_index=True)

    return build_weather_result(final_df, "moyenne climatique")

# ============================================================
# 🧠 AUTO SWITCH
# ============================================================

def get_weather_auto(latitude, longitude, date_debut, date_fin):
    today = date.today()
    forecast_limit = today + timedelta(days=16)

    if isinstance(date_debut, str):
        date_debut = date.fromisoformat(date_debut)
    if isinstance(date_fin, str):
        date_fin = date.fromisoformat(date_fin)

    if date_fin <= today:
        return get_weather_archive(latitude, longitude, date_debut, date_fin)

    if date_debut <= forecast_limit and date_fin <= forecast_limit:
        return get_weather_forecast(latitude, longitude, date_debut, date_fin)

    return get_weather_climate_average(latitude, longitude, date_debut, date_fin)

# ============================================================
# 🌡️ CLIMAT
# ============================================================

def get_climate_zone(temperature: float, pluviometrie: float):
    if temperature >= 25 and pluviometrie >= 800:
        return "tropical"
    elif temperature < 12:
        return "froid"
    elif pluviometrie < 300:
        return "sec"
    else:
        return "tempere"

# ============================================================
# 🌱 SOL
# ============================================================

def get_soil_data(latitude: float, longitude: float):
    return {
        "type_sol": "limoneux",
        "ph": 6.8
    }

# ============================================================
# 🧪 TEST
# ============================================================

if __name__ == "__main__":
    lat, lon = 48.85, 2.35
    debut = date(2026, 4, 1)
    fin = date(2026, 4, 10)

    print("Recherche ville:")
    print(search_cities("Paris")[0])

    print("\nTest météo:")
    weather = get_weather_auto(lat, lon, debut, fin)
    print(weather)

    print("\nZone climatique:")
    print(get_climate_zone(weather["temperature"], weather["pluviometrie"]))