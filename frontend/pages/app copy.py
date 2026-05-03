import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
import time
import os

# Récupération dynamique du chemin du fichier .ico (dans le dossier racine, au même niveau que utils.py)
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
favicon_path = os.path.join(current_dir, "agrisim_ai_logo.ico")

# Configuration de la page
if os.path.exists(favicon_path):
    st.set_page_config(
        page_title="AgriSim AI",
        use_container_width=True=favicon_path,
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_title="AgriSim AI",
        use_container_width=True="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Définition de l'URL de l'API (accessible dans toutes les pages)
API_URL = "http://127.0.0.1:8000"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:           #F0EDE6;
    --surface:      #FAFAF7;
    --surface2:     #F2EFE8;
    --border:       rgba(60,55,40,0.20);
    --border-mid:   rgba(60,55,40,0.30);
    --forest:       #1A3528;
    --forest-mid:   #2D5340;
    --forest-light: #3D7A55;
    --leaf:         #4A7C59;
    --sage:         #7FAF8A;
    --lime:         #B3D98F;
    --mist:         #D4E4CF;
    --terra:        #C05A2E;
    --terra-light:  #D4785A;
    --amber:        #D4941A;
    --ink:          #111111;
    --muted:        #444440;
    --caption:      #77736C;
    --radius:       14px;
    --radius-sm:    8px;
    --shadow:       0 2px 14px rgba(30,58,47,0.07);
}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    color: var(--ink) !important;
}

.stApp { background-color: var(--bg) !important; }

[data-testid="stSidebar"] {
    background-color: var(--forest) !important;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.95) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stTextInput input {
    background: #FFFFFF !important;
    border: 1px solid var(--border-mid) !important;
    border-radius: var(--radius-sm) !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stDateInput > div > div {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: var(--radius-sm) !important;
    color: #FFFFFF !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--terra) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    padding: 12px !important;
    transition: background 0.1s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--terra-light) !important;
}
[data-testid="stSidebar"] label {
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: var(--sage) !important;
    font-weight: 700 !important;
}

.hero {
    background: var(--forest);
    border-radius: 16px;
    padding: 36px 44px;
    margin-bottom: 24px;
}
.hero-eyebrow {
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--sage); margin-bottom: 8px; font-weight: 700;
}
.hero-title {
    font-family: 'DM Serif Display', serif !important;
    font-size: 42px !important; font-weight: 400 !important;
    color: white !important; line-height: 1.15 !important;
    margin: 0 0 10px !important;
}
.hero-title em { font-style: italic; color: var(--sage) !important; }
.hero-sub {
    color: rgba(255,255,255,0.82) !important;
    font-size: 14px !important; line-height: 1.65 !important;
    max-width: 540px; font-weight: 400 !important;
}
.hero-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 18px; }
.hero-chip {
    background: rgba(255,255,255,0.13);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 20px; padding: 4px 13px;
    font-size: 11px; color: #FFFFFF !important; letter-spacing: 0.3px;
}

.section-header {
    font-family: 'DM Serif Display', serif !important;
    font-size: 22px !important; font-weight: 400 !important;
    color: var(--forest) !important; letter-spacing: -0.2px !important;
    margin: 24px 0 4px !important;
}
.section-sub {
    font-size: 13px !important; color: var(--muted) !important;
    margin-bottom: 16px !important;
}

.card {
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border-mid);
    overflow: hidden; margin-bottom: 16px;
}
.card-head {
    padding: 14px 18px 12px;
    border-bottom: 1px solid var(--border);
}
.card-title {
    font-size: 13px !important; font-weight: 600 !important;
    color: var(--forest) !important; margin: 0 !important;
}
.card-body { padding: 14px 18px; }

.data-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 0.5px solid rgba(60,55,40,0.12);
    font-size: 13px;
}
.data-row:last-child { border-bottom: none; }
.data-label { color: var(--caption); font-weight: 600; }
.data-val   { font-weight: 600; color: var(--ink); }

[data-testid="stMetric"] {
    background: var(--surface) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-mid) !important;
    border-left: 3px solid var(--leaf) !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important; color: var(--caption) !important;
    font-weight: 700 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Serif Display', serif !important;
    font-size: 26px !important; color: var(--forest) !important;
    font-weight: 400 !important;
}

.status {
    border-radius: var(--radius); padding: 14px 18px;
    margin: 12px 0; display: flex; align-items: flex-start; gap: 10px;
}
.status-dot { width: 7px; height: 7px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
.status-success { background: rgba(61,122,85,0.08); border: 1px solid rgba(61,122,85,0.35); }
.status-success .status-dot { background: var(--forest-light); }
.status-success h4 { color: var(--forest-light) !important; }
.status-warning { background: rgba(212,148,26,0.08); border: 1px solid rgba(212,148,26,0.35); }
.status-warning .status-dot { background: var(--amber); }
.status-warning h4 { color: #8A5C10 !important; }
.status-danger { background: rgba(192,90,46,0.08); border: 1px solid rgba(192,90,46,0.35); }
.status-danger .status-dot { background: var(--terra); }
.status-danger h4 { color: var(--terra) !important; }
.status h4 {
    font-size: 13px !important; font-weight: 700 !important;
    margin: 0 0 3px !important; font-family: 'Outfit', sans-serif !important;
}
.status p {
    font-size: 13px !important; color: var(--ink) !important;
    margin: 0 !important; line-height: 1.6 !important; font-weight: 500 !important;
}

.interpret-box {
    background: var(--forest); border-radius: var(--radius);
    padding: 22px 26px; margin: 14px 0;
}
.interpret-box-label {
    font-size: 10px; letter-spacing: 2.5px; text-transform: uppercase;
    color: var(--sage); margin-bottom: 8px; font-weight: 700;
}
.interpret-box p {
    color: rgba(255,255,255,0.88) !important;
    font-size: 14px !important; line-height: 1.75 !important;
    margin: 0 !important; font-weight: 400 !important;
}
.interpret-box strong { color: var(--sage) !important; font-weight: 700 !important; }

.meta-chip {
    display: inline-flex;
    background: var(--surface2); border: 1px solid var(--border-mid);
    border-radius: 20px; padding: 4px 11px;
    font-size: 12px; font-weight: 600; color: var(--ink) !important; margin: 2px;
}

.sidebar-logo {
    text-align: center; padding: 18px 0 20px;
    border-bottom: 1px solid rgba(255,255,255,0.14); margin-bottom: 18px;
}
.sidebar-logo-icon { font-size: 34px; line-height: 1; }
.sidebar-logo-name {
    font-family: 'DM Serif Display', serif !important;
    font-size: 19px !important; color: white !important;
    margin-top: 7px !important; font-weight: 400 !important;
}
.sidebar-logo-name em { font-style: italic; color: var(--sage) !important; }
.sidebar-logo-tagline {
    font-size: 10px !important; color: rgba(168,196,162,0.75) !important;
    letter-spacing: 2.5px !important; text-transform: uppercase !important;
    margin-top: 4px !important; font-weight: 700 !important;
}
.sidebar-section { border-top: 1px solid rgba(255,255,255,0.13); margin: 16px 0 12px; padding-top: 12px; }
.city-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(107,158,120,0.22); border: 1px solid rgba(107,158,120,0.45);
    border-radius: 20px; padding: 4px 11px;
    font-size: 12px; color: var(--sage) !important; margin-bottom: 12px; font-weight: 600 !important;
}
.city-pill-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--leaf); flex-shrink: 0; }

.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-mid), transparent);
    border: none; margin: 24px 0;
}
.footer {
    text-align: center; padding: 24px 0 10px;
    font-size: 11px; color: var(--caption) !important;
}
.footer span { color: var(--leaf) !important; font-weight: 700 !important; }

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--surface2) !important; border-radius: 10px !important;
    padding: 3px !important; border: 1px solid var(--border-mid) !important; gap: 2px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; border-radius: var(--radius-sm) !important;
    font-size: 13px !important; font-weight: 600 !important; color: var(--muted) !important;
    font-family: 'Outfit', sans-serif !important; padding: 7px 16px !important; border: none !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--surface) !important; color: var(--forest) !important;
    border: 1px solid var(--border-mid) !important; box-shadow: none !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-mid) !important; overflow: hidden !important;
}
.stDownloadButton > button {
    background: var(--surface) !important; border: 1px solid var(--border-mid) !important;
    border-radius: var(--radius-sm) !important; color: var(--forest) !important;
    font-weight: 600 !important; font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important; transition: background 0.2s !important;
}
.stDownloadButton > button:hover { background: var(--surface2) !important; }

.feat-row {
    display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.feat-name { font-size: 12px; color: var(--caption); width: 120px; flex-shrink: 0; }
.feat-bar {
    flex: 1; height: 18px; background: var(--surface2); border-radius: 3px; overflow: hidden; position: relative;
}
.feat-fill {
    height: 100%; border-radius: 3px;
    display: flex; align-items: center; justify-content: flex-end; padding-right: 6px;
}
.feat-fill span { font-size: 10px; font-family: 'DM Mono', monospace; font-weight: 500; }
.feat-dir { font-size: 11px; width: 14px; text-align: center; flex-shrink: 0; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Intelligence Agricole</div>
    <h1 class="hero-title">AgriYield <em>AI</em></h1>
    <p class="hero-sub">Prédiction du rendement agricole par apprentissage automatique — météo, sol &amp; pratiques culturales.</p>
    <div class="hero-chips">
        <span class="hero-chip">FastAPI</span>
        <span class="hero-chip">Streamlit</span>
        <span class="hero-chip">Machine Learning</span>
        <span class="hero-chip">APIs Météo</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── DATA LOADERS ──────────────────────────────────────────────────────
@st.cache_data
def load_cultures():
    try:
        df = pd.read_csv("../backend/data/cultures_agricoles.csv")
        return df["Culture"].dropna().unique().tolist()
    except Exception:
        return ["Blé", "Maïs", "Riz (paddy)", "Soja", "Orge", "Coton"]

def search_city(query):
    try:
        response = requests.post(f"{API_URL}/cities/search", json={"query": query}, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

cultures = load_cultures()

# ── DONNÉES STATIQUES DASHBOARD ───────────────────────────────────────
MONTHS = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]

TREND_DATA = {
    "Blé":  [5.2,5.4,5.8,6.1,6.5,6.9,7.0,7.2,6.8,6.5,6.2,5.9],
    "Maïs": [7.1,7.4,7.8,8.5,9.2,9.8,10.5,11.2,10.8,10.1,9.4,8.6],
    "Soja": [3.8,4.0,4.3,4.6,5.0,5.3,5.6,6.0,5.7,5.4,5.1,4.7],
}

HEATMAP_CULTURES = ["Blé","Maïs","Soja","Riz","Orge","Coton"]
HEATMAP_PAYS     = ["France","Brésil","Inde","USA","Chine","Australie"]
HEATMAP_VALUES   = [
    [7.2, 5.1, 3.8, 2.1, 5.9, 4.4],
    [5.8, 8.2, 4.2, 3.9, 4.1, 6.7],
    [2.9, 6.4, 7.1, 1.8, 3.2, 5.5],
    [3.8,11.2, 6.0, 7.5, 3.7, 2.8],
    [2.1, 5.8, 4.9, 6.2, 2.8, 3.4],
    [1.8, 4.2, 3.1, 5.8, 2.2, 2.9],
]

TOP_CULTURES_BY_COUNTRY = {
    "France": [("Blé",7.2), ("Orge",5.9), ("Maïs",5.8), ("Colza",3.6), ("Soja",2.9)],
    "Brésil": [("Maïs",8.2), ("Soja",7.1), ("Riz",5.8), ("Coton",4.2), ("Blé",3.8)],
    "Inde":   [("Riz",6.4), ("Soja",4.9), ("Blé",3.8), ("Orge",3.2), ("Maïs",2.9)],
    "USA":    [("Maïs",11.2), ("Riz",7.5), ("Soja",6.0), ("Blé",5.8), ("Coton",4.2)],
}

SHAP_FEATURES = {
    "Blé":  [("Température","pos",78),("Pluviométrie","pos",65),("Engrais N","pos",59),
              ("pH sol","pos",45),("Humidité","neg",38),("Irrigation","pos",30),("Altitude","neg",18)],
    "Maïs": [("Engrais N","pos",85),("Température","pos",72),("Irrigation","pos",68),
              ("Pluviométrie","pos",52),("pH sol","pos",41),("Humidité","pos",34),("Vent","neg",20)],
    "Soja": [("Humidité","pos",80),("Pluviométrie","pos",74),("Température","pos",62),
              ("pH sol","neg",48),("Engrais N","neg",38),("Irrigation","pos",30),("Altitude","neg",22)],
    "Riz":  [("Irrigation","pos",92),("Température","pos",81),("Humidité","pos",76),
              ("Pluviométrie","pos",60),("Engrais N","pos",44),("pH sol","neg",35),("Vent","neg",15)],
}

SHAP_REASONS = {
    "Blé":  "La **température optimale (15–20°C)** est le premier levier. L'engrais azoté booste la protéine du grain. Un excès d'humidité pénalise via la verse et les maladies fongiques.",
    "Maïs": "L'**azote est le facteur limitant principal** du maïs. L'irrigation en phase floraison est déterminante. Température et photopériode restent favorables.",
    "Soja": "La culture est très sensible au **stress hydrique** : humidité et pluviométrie dominent. Un pH élevé réduit la disponibilité du fer. Peu gourmand en N grâce à la fixation.",
    "Riz":  "Le riz est culture **aquatique par excellence** : l'irrigation explique 92% de la variance. La chaleur humide est idéale. Le vent au stade épiaison = risque négatif principal.",
}

SCATTER_DATA = {
    "Céréales": [(50,4.1),(70,5.2),(90,6.0),(110,7.2),(130,7.8),(150,8.5),
                 (60,4.8),(80,5.9),(100,6.7),(140,8.1),(170,9.2),(190,10.1)],
    "Oléagineux":[(40,2.8),(55,3.4),(75,4.2),(95,5.1),(120,6.0),(145,6.8),
                  (65,3.9),(85,4.7),(105,5.5),(125,6.2),(160,7.4),(180,8.0)],
}

PALETTE = {
    "forest":       "#1A3528",
    "leaf":         "#3D7A55",
    "sage":         "#7FAF8A",
    "lime":         "#B3D98F",
    "terra":        "#C05A2E",
    "amber":        "#EF9F27",
    "blue":         "#378ADD",
    "red":          "#E24B4A",
}

# ── SIDEBAR ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🌾</div>
        <div class="sidebar-logo-name">AgriYield <em>AI</em></div>
        <div class="sidebar-logo-tagline">Simulation agricole</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Localisation**")
    city_query = st.text_input("Rechercher une ville", "Paris")

    cities = search_city(city_query) if city_query else []

    if cities:
        city_options = [
            f"{c['name']} — {c.get('admin1', '')} · {c['country']}"
            for c in cities
        ]
        selected_label = st.selectbox("Ville proposée", city_options)
        selected_city  = cities[city_options.index(selected_label)]

        zone      = selected_city["name"]
        country   = selected_city.get("country", "")
        admin1    = selected_city.get("admin1", "")
        latitude  = selected_city["latitude"]
        longitude = selected_city["longitude"]

        st.markdown(f"""
        <div class="city-pill">
            <div class="city-pill-dot"></div>
            {zone}, {admin1}, {country}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Aucune ville trouvée.")
        st.stop()

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    st.markdown("**Culture**")
    culture = st.selectbox("", cultures, label_visibility="collapsed")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    st.markdown("**Pratiques agricoles**")
    engrais    = st.slider("Engrais (kg/ha)", 0, 200, 70, 5)
    irrigation = st.radio("Irrigation", ["oui", "non"], horizontal=True)

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    st.markdown("**Période de culture**")
    d1, d2 = st.columns(2)
    with d1:
        date_debut = st.date_input("Début", value=date.today(), format="DD/MM/YYYY")
    with d2:
        date_fin = st.date_input("Fin",   value=date.today(), format="DD/MM/YYYY")

    if date_debut > date_fin:
        st.error("La date de début doit précéder la date de fin.")
        st.stop()

    st.markdown("<br>", unsafe_allow_html=True)
    predict_button = st.button("Lancer la prédiction", use_container_width=True)

# ── RECOMMANDATION IA ─────────────────────────────────────────────────
try:
    reco_res = requests.post(
        f"{API_URL}/cultures/recommend",
        json={
            "culture": culture, "zone": zone, "latitude": latitude,
            "longitude": longitude, "date_debut": str(date_debut),
            "date_fin": str(date_fin), "engrais": engrais, "irrigation": irrigation
        }, timeout=5
    )
    if reco_res.status_code == 200:
        reco_data = reco_res.json()
        st.markdown(f"""
        <div class="status status-warning">
            <div class="status-dot"></div>
            <div>
                <h4>Suggestion IA (climat : {reco_data['climat']})</h4>
                <p>👉 {', '.join(reco_data['cultures'])}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
except Exception:
    pass

# ── TABS ───────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Prédiction & Résultats",
    "Historique",
    "IA Explicable",
    "Performances ML",
])

# ══════════════════════════════════════════════════════════════════════
# TAB 0 — DASHBOARD PRO
# ══════════════════════════════════════════════════════════════════════
with tab0:
    st.markdown('<div class="section-header">Dashboard Analytique Réel</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Analyse basée sur les prédictions réellement enregistrées dans la base.</p>',
        unsafe_allow_html=True
    )

    try:
        history_response = requests.get(f"{API_URL}/history", timeout=10)

        if history_response.status_code != 200:
            st.error("Impossible de récupérer l’historique depuis l’API.")
            st.stop()

        history = history_response.json()

        if not history:
            st.info("Aucune prédiction enregistrée pour le moment.")
            st.stop()

        df_dash = pd.DataFrame(history)

        if "date_prediction" in df_dash.columns:
            df_dash["date_prediction"] = pd.to_datetime(df_dash["date_prediction"])

        # ── KPIs réels ─────────────────────────────
        rendement_moyen = df_dash["rendement_predit"].mean()
        rendement_max = df_dash["rendement_predit"].max()
        rendement_min = df_dash["rendement_predit"].min()
        nb_predictions = len(df_dash)

        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Nombre de prédictions", nb_predictions)
        k2.metric("Rendement moyen", f"{rendement_moyen:.2f} t/ha")
        k3.metric("Meilleur rendement", f"{rendement_max:.2f} t/ha")
        k4.metric("Rendement minimum", f"{rendement_min:.2f} t/ha")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Filtres ─────────────────────────────
        st.markdown('<div class="section-header">Filtres</div>', unsafe_allow_html=True)

        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            cultures = ["Toutes"] + sorted(df_dash["culture"].dropna().unique().tolist())
            selected_culture = st.selectbox("Culture", cultures)

        with col_f2:
            zones = ["Toutes"] + sorted(df_dash["zone"].dropna().unique().tolist())
            selected_zone = st.selectbox("Zone", zones)

        with col_f3:
            irrigations = ["Toutes"] + sorted(df_dash["irrigation"].dropna().unique().tolist())
            selected_irrigation = st.selectbox("Irrigation", irrigations)

        df_filtered = df_dash.copy()

        if selected_culture != "Toutes":
            df_filtered = df_filtered[df_filtered["culture"] == selected_culture]

        if selected_zone != "Toutes":
            df_filtered = df_filtered[df_filtered["zone"] == selected_zone]

        if selected_irrigation != "Toutes":
            df_filtered = df_filtered[df_filtered["irrigation"] == selected_irrigation]

        if df_filtered.empty:
            st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
            st.stop()

        # ── Tableau réel ─────────────────────────────
        st.markdown('<div class="section-header">Données utilisées</div>', unsafe_allow_html=True)
        st.dataframe(df_filtered, use_container_width=True)

        csv_dash = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Télécharger les données du dashboard",
            data=csv_dash,
            file_name="dashboard_predictions.csv",
            mime="text/csv",
            use_container_width=True
        )

        # ── Heatmap réelle : culture × zone ─────────────────────────────
        st.markdown('<div class="section-header">Heatmap rendement — culture × zone</div>', unsafe_allow_html=True)

        heat_df = df_filtered.pivot_table(
            values="rendement_predit",
            index="culture",
            columns="zone",
            aggfunc="mean"
        )

        if not heat_df.empty:
            fig_heat = px.imshow(
                heat_df,
                text_auto=".2f",
                aspect="auto",
                title="Rendement moyen par culture et par zone",
                labels=dict(
                    x="Zone",
                    y="Culture",
                    color="Rendement moyen"
                )
            )

            fig_heat.update_layout(
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#444440")
            )

            st.plotly_chart(fig_heat, use_container_width=True)

        # ── Évolution réelle des rendements ─────────────────────────────
        if "date_prediction" in df_filtered.columns:
            st.markdown('<div class="section-header">Évolution des rendements</div>', unsafe_allow_html=True)

            fig_line = px.line(
                df_filtered.sort_values("date_prediction"),
                x="date_prediction",
                y="rendement_predit",
                color="culture",
                markers=True,
                title="Évolution réelle des rendements prédits",
                labels={
                    "date_prediction": "Date",
                    "rendement_predit": "Rendement prédit (t/ha)",
                    "culture": "Culture"
                }
            )

            fig_line.update_layout(
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#444440")
            )

            st.plotly_chart(fig_line, use_container_width=True)

        # ── Rendement moyen par culture ─────────────────────────────
        st.markdown('<div class="section-header">Rendement moyen par culture</div>', unsafe_allow_html=True)

        culture_stats = (
            df_filtered.groupby("culture")["rendement_predit"]
            .mean()
            .reset_index()
            .sort_values("rendement_predit", ascending=False)
        )

        fig_culture = px.bar(
            culture_stats,
            x="culture",
            y="rendement_predit",
            title="Classement réel des cultures par rendement moyen",
            labels={
                "culture": "Culture",
                "rendement_predit": "Rendement moyen (t/ha)"
            }
        )

        fig_culture.update_layout(
            height=420,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#444440")
        )

        st.plotly_chart(fig_culture, use_container_width=True)

        # ── Corrélation engrais / rendement réelle ─────────────────────────────
        st.markdown('<div class="section-header">Corrélation engrais / rendement</div>', unsafe_allow_html=True)

        fig_scatter = px.scatter(
            df_filtered,
            x="engrais",
            y="rendement_predit",
            color="culture",
            size="pluviometrie",
            hover_data=["zone", "temperature", "humidite", "irrigation"],
            title="Impact réel de l’engrais sur le rendement",
            labels={
                "engrais": "Engrais (kg/ha)",
                "rendement_predit": "Rendement prédit (t/ha)",
                "culture": "Culture"
            }
        )

        fig_scatter.update_layout(
            height=460,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#444440")
        )

        st.plotly_chart(fig_scatter, use_container_width=True)

        # ── Top zones réelles ─────────────────────────────
        st.markdown('<div class="section-header">Top zones par rendement moyen</div>', unsafe_allow_html=True)

        zone_stats = (
            df_filtered.groupby("zone")["rendement_predit"]
            .mean()
            .reset_index()
            .sort_values("rendement_predit", ascending=False)
        )

        fig_zone = px.bar(
            zone_stats,
            x="rendement_predit",
            y="zone",
            orientation="h",
            title="Zones avec les meilleurs rendements moyens",
            labels={
                "zone": "Zone",
                "rendement_predit": "Rendement moyen (t/ha)"
            }
        )

        fig_zone.update_layout(
            height=420,
            yaxis={"categoryorder": "total ascending"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#444440")
        )

        st.plotly_chart(fig_zone, use_container_width=True)

        # ── Carte réelle ─────────────────────────────
        if "latitude" in df_filtered.columns and "longitude" in df_filtered.columns:
            st.markdown('<div class="section-header">Carte des prédictions enregistrées</div>', unsafe_allow_html=True)

            map_df = df_filtered.rename(
                columns={
                    "latitude": "lat",
                    "longitude": "lon"
                }
            )

            st.map(map_df[["lat", "lon"]])

        # ── Insight automatique réel ─────────────────────────────
        st.markdown('<div class="section-header">Analyse automatique</div>', unsafe_allow_html=True)

        best_row = df_filtered.sort_values("rendement_predit", ascending=False).iloc[0]
        worst_row = df_filtered.sort_values("rendement_predit", ascending=True).iloc[0]

        st.markdown(f"""
        <div class="interpret-box">
            <div class="interpret-box-label">Insight IA</div>
            <p>
                Le meilleur rendement enregistré concerne <strong>{best_row['culture']}</strong>
                à <strong>{best_row['zone']}</strong>, avec
                <strong>{best_row['rendement_predit']} t/ha</strong>.
                Le rendement le plus faible concerne <strong>{worst_row['culture']}</strong>
                à <strong>{worst_row['zone']}</strong>, avec
                <strong>{worst_row['rendement_predit']} t/ha</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur dashboard réel : {e}")

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — PRÉDICTION
# ══════════════════════════════════════════════════════════════════════
with tab1:
    col_map, col_info = st.columns([1.3, 1], gap="large")

    with col_map:
        st.markdown('<div class="card"><div class="card-head"><div class="card-title">Localisation sélectionnée</div></div><div class="card-body">', unsafe_allow_html=True)
        st.map(pd.DataFrame({"lat": [latitude], "lon": [longitude]}), zoom=5)
        st.markdown(f"""
        <div style="margin-top:10px;">
            <span class="meta-chip">Latitude : {latitude:.4f}</span>
            <span class="meta-chip">Longitude : {longitude:.4f}</span>
            <span class="meta-chip">Pays : {country}</span>
        </div>
        </div></div>""", unsafe_allow_html=True)

    with col_info:
        st.markdown('<div class="card"><div class="card-head"><div class="card-title">Paramètres de simulation</div></div><div class="card-body">', unsafe_allow_html=True)
        for label, val in [
            ("Culture", culture), ("Zone", zone), ("Pays", country),
            ("Engrais", f"{engrais} kg/ha"), ("Irrigation", irrigation.capitalize()),
            ("Début", str(date_debut)), ("Fin", str(date_fin)),
        ]:
            st.markdown(f"""
            <div class="data-row">
                <span class="data-label">{label}</span>
                <span class="data-val">{val}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    if predict_button:
        data = {
            "culture": culture, "zone": zone, "latitude": latitude, "longitude": longitude,
            "engrais": engrais, "irrigation": irrigation,
            "date_debut": str(date_debut), "date_fin": str(date_fin)
        }
        try:
            progress_text = "Analyse des données et calcul de prédiction en cours…"
            bar = st.progress(0, text=progress_text)
            for i in range(100):
                time.sleep(0.015)
                bar.progress(i + 1, text=progress_text)

            response = requests.post(f"{API_URL}/predict", json=data, timeout=25)
            bar.empty()

            if response.status_code == 200:
                result     = response.json()
                result_df  = pd.DataFrame([result])
                csv_result = result_df.to_csv(index=False).encode("utf-8")

                st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Résumé décisionnel</div>', unsafe_allow_html=True)

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Rendement prédit",  f"{result['rendement_predit']} t/ha")
                k2.metric("Température moy.",  f"{result['temperature']} °C")
                k3.metric("Humidité moy.",     f"{result['humidite']} %")
                k4.metric("Pluviométrie",      f"{result['pluviometrie']} mm")

                st.markdown(f"""
                <div class="status status-success">
                    <div class="status-dot"></div>
                    <div>
                        <h4>Source météo utilisée</h4>
                        <p><strong>{result.get('source_meteo','Non précisée')}</strong> — Données climatiques de référence pour cette région.</p>
                    </div>
                </div>""", unsafe_allow_html=True)

                st.download_button(
                    "Télécharger cette prédiction (CSV)", data=csv_result,
                    file_name="prediction_rendement.csv", mime="text/csv", use_container_width=True
                )

                d1, d2 = st.columns(2, gap="large")
                with d1:
                    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Environnement & Climat</div></div><div class="card-body">', unsafe_allow_html=True)
                    for label, val in [
                        ("Zone", result["zone"]), ("Période", f"{date_debut} → {date_fin}"),
                        ("Température", f"{result['temperature']} °C"), ("Humidité", f"{result['humidite']} %"),
                        ("Pluviométrie", f"{result['pluviometrie']} mm"), ("Type de sol", result["type_sol"]),
                        ("pH du sol", result["ph"]),
                    ]:
                        st.markdown(f'<div class="data-row"><span class="data-label">{label}</span><span class="data-val">{val}</span></div>', unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                with d2:
                    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Pratiques agricoles</div></div><div class="card-body">', unsafe_allow_html=True)
                    for label, val in [
                        ("Culture", result["culture"]), ("Engrais", f"{result['engrais']} kg/ha"),
                        ("Irrigation", result["irrigation"]), ("Latitude", result["latitude"]),
                        ("Longitude", result["longitude"]),
                    ]:
                        st.markdown(f'<div class="data-row"><span class="data-label">{label}</span><span class="data-val">{val}</span></div>', unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown('<div class="section-header">Interprétation automatique</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="interpret-box">
                    <div class="interpret-box-label">Analyse du modèle</div>
                    <p>Pour la culture <strong>{result['culture']}</strong> dans la zone <strong>{result['zone']}</strong>,
                    le modèle estime un rendement de <strong>{result['rendement_predit']} t/ha</strong>.
                    Cette prédiction intègre l'historique météorologique récent et les conditions du sol locales.</p>
                </div>""", unsafe_allow_html=True)

                rendement = result["rendement_predit"]
                if rendement < 3:
                    st.markdown("""
                    <div class="status status-danger">
                        <div class="status-dot"></div>
                        <div><h4>Rendement faible — Action requise</h4>
                        <p>Améliorer l'irrigation, analyser le sol, ajuster la fertilisation et vérifier la présence de stress hydrique ou thermique.</p></div>
                    </div>""", unsafe_allow_html=True)
                elif rendement < 5:
                    st.markdown("""
                    <div class="status status-warning">
                        <div class="status-dot"></div>
                        <div><h4>Rendement moyen — Optimisation possible</h4>
                        <p>Optimiser la gestion de l'eau, le suivi climatique et la fertilisation pour maximiser la production.</p></div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="status status-success">
                        <div class="status-dot"></div>
                        <div><h4>Bon rendement — Conditions favorables</h4>
                        <p>Les conditions semblent très favorables. Maintenir les pratiques actuelles et surveiller les conditions climatiques.</p></div>
                    </div>""", unsafe_allow_html=True)

            else:
                st.error(f"Erreur API ({response.status_code}) : {response.text}")
        except Exception as e:
            st.error(f"Impossible de contacter le backend : {e}")


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORIQUE
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Historique des prédictions</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Consultez l\'ensemble des anciennes simulations. Vous pouvez les exporter en CSV.</p>', unsafe_allow_html=True)

    if st.button("Actualiser l'historique", use_container_width=True):
        try:
            history_response = requests.get(f"{API_URL}/history", timeout=10)
            if history_response.status_code == 200:
                history = history_response.json()
                if history:
                    df_history = pd.DataFrame(history)
                    st.dataframe(df_history, use_container_width=True)

                    csv_history = df_history.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Télécharger l'historique (CSV)", data=csv_history,
                        file_name="historique_predictions.csv", mime="text/csv", use_container_width=True
                    )

                    if "date_prediction" in df_history.columns:
                        df_history["date_prediction"] = pd.to_datetime(df_history["date_prediction"])

                    if "rendement_predit" in df_history.columns:
                        st.markdown('<div class="section-header">Évolution des rendements</div>', unsafe_allow_html=True)
                        fig_hist = go.Figure(go.Scatter(
                            x=df_history.sort_values("date_prediction")["date_prediction"],
                            y=df_history.sort_values("date_prediction")["rendement_predit"],
                            mode="lines+markers",
                            line=dict(color=PALETTE["leaf"], width=2),
                            marker=dict(size=6, color=PALETTE["forest"]),
                            fill="tozeroy", fillcolor="rgba(61,122,85,0.08)",
                        ))
                        fig_hist.update_layout(
                            height=360,
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="Outfit", color="#444440"),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(gridcolor="rgba(100,100,100,0.12)", title="t/ha"),
                            margin=dict(t=10, b=10, l=10, r=10),
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)

                    if "latitude" in df_history.columns and "longitude" in df_history.columns:
                        st.markdown('<div class="section-header">Carte des prédictions</div>', unsafe_allow_html=True)
                        map_df = df_history.rename(columns={"latitude": "lat", "longitude": "lon"})
                        st.map(map_df[["lat", "lon"]])
                else:
                    st.info("Aucune prédiction enregistrée.")
        except Exception as e:
            st.error(f"Erreur historique : {e}")


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — IA EXPLICABLE (SHAP)
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">IA Explicable — Importance des features</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Visualisation SHAP : pourquoi le modèle prédit ce rendement ? Sélectionnez une culture pour voir l\'impact de chaque variable.</p>', unsafe_allow_html=True)

    col_sel, _ = st.columns([1, 2])
    with col_sel:
        shap_culture = st.selectbox(
            "Culture analysée",
            [c for c in SHAP_FEATURES.keys()],
            label_visibility="collapsed"
        )

    feats = SHAP_FEATURES.get(shap_culture, [])

    # Score ring (simulé via gauge Plotly)
    col_ring, col_bars = st.columns([1, 2], gap="large")

    with col_ring:
        st.markdown('<div class="card"><div class="card-head"><div class="card-title">Score de performance IA</div></div><div class="card-body">', unsafe_allow_html=True)
        score_map = {"Blé": 82, "Maïs": 91, "Soja": 87, "Riz": 94}
        score = score_map.get(shap_culture, 87)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#77736C", "tickfont": dict(size=10)},
                "bar": {"color": PALETTE["leaf"], "thickness": 0.25},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 60],  "color": "#EAF3DE"},
                    {"range": [60, 80], "color": "#B3D98F"},
                    {"range": [80, 100],"color": "#7FAF8A"},
                ],
                "threshold": {"line": {"color": PALETTE["forest"], "width": 3}, "value": score}
            },
            number={"font": {"size": 36, "family": "DM Serif Display", "color": PALETTE["forest"]}, "suffix": " / 100"}
        ))
        fig_gauge.update_layout(
            height=200, margin=dict(t=20, b=10, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit"),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(f"""
        <div style="margin-top:4px">
            {"".join([f'<div class="data-row"><span class="data-label">{lbl}</span><span class="data-val">{val}%</span></div>'
              for lbl, val in [("Précision prédiction","94"),("Couverture météo","88"),("Qualité sol","81"),("Richesse données","79")]])}
        </div>
        </div></div>""", unsafe_allow_html=True)

    with col_bars:
        st.markdown('<div class="card"><div class="card-head"><div class="card-title">Importance des variables (SHAP)</div></div><div class="card-body">', unsafe_allow_html=True)

        # Graphique barres horizontales SHAP
        feat_names = [f[0] for f in feats]
        feat_vals  = [f[2] if f[1] == "pos" else -f[2] for f in feats]
        feat_colors = [PALETTE["leaf"] if v > 0 else PALETTE["terra"] for v in feat_vals]

        fig_shap = go.Figure(go.Bar(
            y=feat_names,
            x=feat_vals,
            orientation="h",
            marker_color=feat_colors,
            text=[f"+{abs(v)}%" if v > 0 else f"-{abs(v)}%" for v in feat_vals],
            textposition="outside",
            textfont=dict(size=11, family="DM Mono"),
            hovertemplate="<b>%{y}</b><br>Impact SHAP : %{x}%<extra></extra>",
        ))
        fig_shap.add_vline(x=0, line_color="#444440", line_width=1)
        fig_shap.update_layout(
            height=280, margin=dict(t=10, b=10, l=10, r=60),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit", color="#444440"),
            xaxis=dict(
                title="Impact relatif (%)", gridcolor="rgba(100,100,100,0.12)",
                tickfont=dict(size=10), zeroline=False
            ),
            yaxis=dict(tickfont=dict(size=12), autorange="reversed"),
        )
        st.plotly_chart(fig_shap, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Radar chart des features
    st.markdown('<div class="section-header">Profil radar — facteurs influents</div>', unsafe_allow_html=True)
    positive_feats = [(n, v) for n, d, v in feats if d == "pos"]
    radar_labels = [f[0] for f in positive_feats]
    radar_vals   = [f[1] for f in positive_feats]
    radar_labels_closed = radar_labels + [radar_labels[0]]
    radar_vals_closed   = radar_vals   + [radar_vals[0]]

    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_vals_closed, theta=radar_labels_closed,
        fill="toself", fillcolor="rgba(61,122,85,0.15)",
        line=dict(color=PALETTE["leaf"], width=2),
        marker=dict(size=6, color=PALETTE["forest"]),
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9), gridcolor="rgba(100,100,100,0.2)"),
            angularaxis=dict(tickfont=dict(size=11, family="Outfit")),
        ),
        height=320, margin=dict(t=20, b=20, l=40, r=40),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Explication textuelle
    reason = SHAP_REASONS.get(shap_culture, "")
    st.markdown(f"""
    <div class="interpret-box">
        <div class="interpret-box-label">Pourquoi ce rendement ? — {shap_culture}</div>
        <p>{reason}</p>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 4 — PERFORMANCES ML
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Comparaison des modèles ML</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Évaluation des modèles selon les métriques standards : MAE, RMSE et R².</p>', unsafe_allow_html=True)

    try:
        df_results = pd.read_csv("../backend/model/model_v5_results.csv")
        st.dataframe(df_results, use_container_width=True)

        csv_results = df_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Télécharger les performances ML (CSV)", data=csv_results,
            file_name="performances_modeles.csv", mime="text/csv", use_container_width=True
        )

        # Graphique comparaison modèles si colonnes disponibles
        if {"Modèle", "R2", "MAE"}.issubset(df_results.columns):
            col_r2, col_mae = st.columns(2, gap="large")

            with col_r2:
                fig_r2 = go.Figure(go.Bar(
                    x=df_results["Modèle"], y=df_results["R2"],
                    marker_color=PALETTE["leaf"],
                    text=[f"{v:.3f}" for v in df_results["R2"]],
                    textposition="outside",
                ))
                fig_r2.update_layout(
                    title="R² par modèle", height=280,
                    margin=dict(t=30,b=10,l=10,r=10),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Outfit", color="#444440"),
                    yaxis=dict(range=[0, 1], gridcolor="rgba(100,100,100,0.12)"),
                    xaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_r2, use_container_width=True)

            with col_mae:
                fig_mae = go.Figure(go.Bar(
                    x=df_results["Modèle"], y=df_results["MAE"],
                    marker_color=PALETTE["amber"],
                    text=[f"{v:.3f}" for v in df_results["MAE"]],
                    textposition="outside",
                ))
                fig_mae.update_layout(
                    title="MAE par modèle", height=280,
                    margin=dict(t=30,b=10,l=10,r=10),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Outfit", color="#444440"),
                    yaxis=dict(gridcolor="rgba(100,100,100,0.12)"),
                    xaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig_mae, use_container_width=True)

    except Exception:
        st.info("Aucun résultat de modèle trouvé. Exécutez le script d'entraînement pour générer le fichier.")

        # Données de démo si fichier absent
        st.markdown('<p class="section-sub">Exemple de visualisation avec données de démonstration :</p>', unsafe_allow_html=True)
        demo_models = pd.DataFrame({
            "Modèle": ["Random Forest", "XGBoost", "Ridge", "SVR"],
            "R2":  [0.94, 0.92, 0.85, 0.88],
            "MAE": [0.31, 0.36, 0.54, 0.44],
            "RMSE":[0.42, 0.48, 0.67, 0.55],
        })

        col_r2, col_mae = st.columns(2, gap="large")
        with col_r2:
            fig_r2d = go.Figure(go.Bar(
                x=demo_models["Modèle"], y=demo_models["R2"],
                marker_color=[PALETTE["forest"], PALETTE["leaf"], PALETTE["sage"], PALETTE["lime"]],
                text=[f"{v:.2f}" for v in demo_models["R2"]], textposition="outside",
            ))
            fig_r2d.update_layout(
                title="R² par modèle (démo)", height=280,
                margin=dict(t=30,b=10,l=10,r=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#444440"),
                yaxis=dict(range=[0, 1.1], gridcolor="rgba(100,100,100,0.12)"),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_r2d, use_container_width=True)

        with col_mae:
            fig_maed = go.Figure(go.Bar(
                x=demo_models["Modèle"], y=demo_models["MAE"],
                marker_color=[PALETTE["forest"], PALETTE["leaf"], PALETTE["sage"], PALETTE["lime"]],
                text=[f"{v:.2f}" for v in demo_models["MAE"]], textposition="outside",
            ))
            fig_maed.update_layout(
                title="MAE par modèle (démo)", height=280,
                margin=dict(t=30,b=10,l=10,r=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#444440"),
                yaxis=dict(gridcolor="rgba(100,100,100,0.12)"),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_maed, use_container_width=True)


# ── FOOTER ─────────────────────────────────────────────────────────────
st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    AgriYield <span>AI</span> — Simulation agricole intelligente &nbsp;·&nbsp;
    Powered by FastAPI · Streamlit · Scikit-learn
</div>
""", unsafe_allow_html=True)