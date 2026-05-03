# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# pages/2_Prediction.py — AgriSim AI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

from utils import (
    CSS, PAL, CONFIG,
    sidebar_logo, sidebar_location,
    load_cultures, footer,
    status_html, progress_bar_html, show_api_error,
)

# ── Config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Prédiction — AgriSim AI",
    page_icon="🌱",
    layout="wide",
)
st.markdown(CSS, unsafe_allow_html=True)

cultures = load_cultures()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers locaux
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _rendement_level(rend: float) -> tuple[str, str, str]:
    """Retourne (level, titre, body) selon le rendement prédit."""
    if rend < 3:
        return ("danger",
                "Rendement faible — Action requise",
                "Améliorer l'irrigation, analyser le sol et ajuster la fertilisation.")
    if rend < 5:
        return ("warning",
                "Rendement moyen — Optimisation possible",
                "Optimiser la gestion de l'eau, le suivi climatique et la fertilisation.")
    return ("success",
            "Bon rendement — Conditions favorables",
            "Maintenir les pratiques actuelles et surveiller les conditions climatiques.")


def _data_row(label: str, value: str) -> str:
    return (
        f'<div class="data-row">'
        f'<span class="data-label">{label}</span>'
        f'<span class="data-val">{value}</span>'
        f'</div>'
    )


def _card(title: str, rows: list[tuple[str, str]]) -> str:
    rows_html = "".join(_data_row(l, v) for l, v in rows)
    return (
        f'<div class="card">'
        f'<div class="card-head"><div class="card-title">{title}</div></div>'
        f'<div class="card-body">{rows_html}</div>'
        f'</div>'
    )


def _fetch_recommendation(payload: dict) -> dict | None:
    try:
        r = requests.post(
            f"{CONFIG.api_url}/cultures/recommend",
            json=payload, timeout=5,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _run_prediction(payload: dict) -> dict | None:
    try:
        r = requests.post(
            f"{CONFIG.api_url}/predict",
            json=payload, timeout=25,
        )
        if r.status_code == 200:
            return r.json()
        st.error(f"Erreur API ({r.status_code}) : {r.text}")
    except Exception as e:
        show_api_error(str(e))
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sidebar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    sidebar_logo()

    st.page_link("app.py",                     label="🏠  Accueil")
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard")
    st.page_link("pages/2_Prediction.py",      label="🌱  Prédiction")
    st.page_link("pages/3_Historique.py",      label="📋  Historique")
    st.page_link("pages/4_IA_Explicable.py",   label="🔍  IA Explicable")
    st.page_link("pages/5_Performances_ML.py", label="⚙️  Performances ML")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)

    # — Localisation (helper centralisé) —
    loc = sidebar_location()
    if not loc:
        st.stop()
    zone      = loc["zone"]
    country   = loc["country"]
    admin1    = loc["admin1"]
    latitude  = loc["latitude"]
    longitude = loc["longitude"]

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)

    # — Culture —
    st.markdown("**Culture**")
    culture = st.selectbox("", cultures, label_visibility="collapsed")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)

    # — Pratiques —
    st.markdown("**Pratiques agricoles**")
    engrais    = st.slider("Engrais (kg/ha)", 0, 200, 70, step=5)
    irrigation = st.radio("Irrigation", ["oui", "non"], horizontal=True)

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)

    # — Période —
    st.markdown("**Période de culture**")
    dc1, dc2 = st.columns(2)
    with dc1:
        date_debut = st.date_input("Début", value=date.today(), format="DD/MM/YYYY")
    with dc2:
        date_fin = st.date_input(
            "Fin",
            value=date.today() + timedelta(days=90),
            format="DD/MM/YYYY",
        )

    if date_debut > date_fin:
        st.error("La date de début doit précéder la date de fin.")
        st.stop()

    duree_jours = (date_fin - date_debut).days
    st.markdown(
        f'<p style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:4px;">'
        f'Durée : <strong style="color:rgba(255,255,255,0.80);">{duree_jours} jours</strong></p>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    predict_button = st.button("🌱  Lancer la prédiction", use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Corps principal
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# — Recommandation IA —
reco_payload = {
    "culture": culture, "zone": zone,
    "latitude": latitude, "longitude": longitude,
    "date_debut": str(date_debut), "date_fin": str(date_fin),
    "engrais": engrais, "irrigation": irrigation,
}
reco = _fetch_recommendation(reco_payload)
if reco:
    cultures_sugg = ", ".join(reco.get("cultures", []))
    climat        = reco.get("climat", "—")
    st.markdown(
        status_html(
            "warning",
            f"Suggestion IA — Climat : {climat}",
            f"Cultures recommandées pour cette zone : {cultures_sugg}",
        ),
        unsafe_allow_html=True,
    )

# — Titre de section —
st.markdown(
    '<div class="section-header">Simulation de rendement</div>'
    '<p class="section-sub">Renseignez les paramètres dans la barre latérale puis lancez la prédiction.</p>',
    unsafe_allow_html=True,
)

# — Carte + Paramètres —
col_map, col_info = st.columns([1.4, 1], gap="large")

with col_map:
    st.markdown(
        '<div class="card">'
        '<div class="card-head"><div class="card-title">Localisation sélectionnée</div></div>'
        '<div class="card-body">',
        unsafe_allow_html=True,
    )
    st.map(pd.DataFrame({"lat": [latitude], "lon": [longitude]}), zoom=5)
    st.markdown(
        f'<div style="margin-top:10px;">'
        f'<span class="meta-chip">📍 {zone}, {admin1}</span>'
        f'<span class="meta-chip">Lat {latitude:.4f}</span>'
        f'<span class="meta-chip">Lon {longitude:.4f}</span>'
        f'<span class="meta-chip">{country}</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

with col_info:
    st.markdown(
        _card("Paramètres de simulation", [
            ("Culture",    culture),
            ("Zone",       zone),
            ("Pays",       country),
            ("Engrais",    f"{engrais} kg/ha"),
            ("Irrigation", irrigation.capitalize()),
            ("Début",      str(date_debut)),
            ("Fin",        str(date_fin)),
            ("Durée",      f"{duree_jours} jours"),
        ]),
        unsafe_allow_html=True,
    )

    # Aperçu engrais via barre de progression
    st.markdown(
        f'<p style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;'
        f'font-weight:700;color:var(--caption);margin:16px 0 5px;">Dose engrais</p>'
        f'{progress_bar_html(engrais, max_value=200)}',
        unsafe_allow_html=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Prédiction
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if predict_button:
    payload = {
        "culture":    culture,    "zone":      zone,
        "latitude":   latitude,   "longitude": longitude,
        "engrais":    engrais,    "irrigation": irrigation,
        "date_debut": str(date_debut), "date_fin": str(date_fin),
    }

    # Barre de progression animée
    prog = st.progress(0, text="Récupération des données météo…")
    for i in range(40):
        time.sleep(0.012)
        prog.progress(i + 1, text="Récupération des données météo…")
    prog.progress(40, text="Inférence du modèle ML…")
    for i in range(40, 95):
        time.sleep(0.010)
        prog.progress(i + 1, text="Inférence du modèle ML…")

    r = _run_prediction(payload)
    prog.empty()

    if r is None:
        st.stop()

    # — Cache invalidation —
    st.cache_data.clear()

    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)

    # ── Métriques clés ─────────────────────────────────────────
    st.markdown('<div class="section-header">Résumé décisionnel</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rendement prédit",  f"{r['rendement_predit']} t/ha")
    m2.metric("Température moy.",  f"{r['temperature']} °C")
    m3.metric("Humidité moy.",     f"{r['humidite']} %")
    m4.metric("Pluviométrie",      f"{r['pluviometrie']} mm")

    # ── Source météo + export ──────────────────────────────────
    src_meteo = r.get("source_meteo", "Non précisée")
    st.markdown(
        status_html("success", "Source météo", src_meteo),
        unsafe_allow_html=True,
    )

    csv_data = pd.DataFrame([r]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Télécharger cette prédiction (CSV)",
        data=csv_data,
        file_name=f"prediction_{culture}_{zone}_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ── Détails environnement & pratiques ─────────────────────
    d1, d2 = st.columns(2, gap="large")
    with d1:
        st.markdown(
            _card("Environnement & Climat", [
                ("Zone",         r["zone"]),
                ("Période",      f"{date_debut} → {date_fin}"),
                ("Durée",        f"{duree_jours} jours"),
                ("Température",  f"{r['temperature']} °C"),
                ("Humidité",     f"{r['humidite']} %"),
                ("Pluviométrie", f"{r['pluviometrie']} mm"),
                ("Type de sol",  r["type_sol"]),
                ("pH",           r["ph"]),
            ]),
            unsafe_allow_html=True,
        )
    with d2:
        st.markdown(
            _card("Pratiques agricoles", [
                ("Culture",    r["culture"]),
                ("Engrais",    f"{r['engrais']} kg/ha"),
                ("Irrigation", r["irrigation"].capitalize()),
                ("Latitude",   str(r["latitude"])),
                ("Longitude",  str(r["longitude"])),
            ]),
            unsafe_allow_html=True,
        )
        # Barre engrais dans les résultats
        st.markdown(
            f'<p style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;'
            f'font-weight:700;color:var(--caption);margin:4px 0 5px;">Dose engrais</p>'
            f'{progress_bar_html(r["engrais"], max_value=200)}',
            unsafe_allow_html=True,
        )

    # ── Analyse narrative ──────────────────────────────────────
    st.markdown(f"""
    <div class="interpret-box">
        <div class="interpret-box-label">Analyse du modèle</div>
        <p>Pour la culture <strong>{r['culture']}</strong> à <strong>{r['zone']}</strong>,
        le modèle estime un rendement de <strong>{r['rendement_predit']} t/ha</strong>.
        Cette prédiction intègre la météo récente ({r['temperature']} °C, {r['pluviometrie']} mm)
        et les caractéristiques du sol local (pH {r['ph']}, {r['type_sol']}).</p>
    </div>""", unsafe_allow_html=True)

    # ── Alerte rendement ───────────────────────────────────────
    level, titre, body = _rendement_level(r["rendement_predit"])
    st.markdown(status_html(level, titre, body), unsafe_allow_html=True)

footer()