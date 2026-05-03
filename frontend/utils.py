# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# utils.py  —  Constantes, palette, CSS, helpers partagés
# AgriSim AI — Refactoring v2.0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Configuration centralisée ─────────────────────────────────
@dataclass(frozen=True)
class AppConfig:
    api_url: str = os.getenv("API_URL", "http://127.0.0.1:8000")
    api_timeout: int = 10
    history_ttl: int = 30          # secondes
    request_retries: int = 2
    request_backoff: float = 0.4   # secondes entre retries

CONFIG = AppConfig()

# ── Palette ───────────────────────────────────────────────────
@dataclass(frozen=True)
class Palette:
    forest:  str = "#1A3528"
    leaf:    str = "#3D7A55"
    sage:    str = "#7FAF8A"
    lime:    str = "#B3D98F"
    terra:   str = "#C05A2E"
    amber:   str = "#EF9F27"
    blue:    str = "#378ADD"
    red:     str = "#E24B4A"
    ink:     str = "#111111"
    muted:   str = "#444440"
    caption: str = "#77736C"
    bg:      str = "#F0EDE6"
    surface: str = "#FAFAF7"

PAL = Palette()

CHART_COLORS: list[str] = [
    PAL.forest, PAL.leaf, PAL.sage, PAL.terra,
    PAL.amber,  PAL.blue, PAL.lime, PAL.red,
]

CHART_LAYOUT: dict = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit", color=PAL.muted),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ── Données SHAP ──────────────────────────────────────────────
# Structure : (label, direction, importance_score)
ShapEntry = tuple[str, str, int]

SHAP_FEATURES: dict[str, list[ShapEntry]] = {
    "Blé":      [("Température","pos",78),("Pluviométrie","pos",65),("Engrais N","pos",59),
                 ("pH sol","pos",45),("Humidité","neg",38),("Irrigation","pos",30),("Altitude","neg",18)],
    "Maïs":     [("Engrais N","pos",85),("Température","pos",72),("Irrigation","pos",68),
                 ("Pluviométrie","pos",52),("pH sol","pos",41),("Humidité","pos",34),("Vent","neg",20)],
    "Soja":     [("Humidité","pos",80),("Pluviométrie","pos",74),("Température","pos",62),
                 ("pH sol","neg",48),("Engrais N","neg",38),("Irrigation","pos",30),("Altitude","neg",22)],
    "Riz":      [("Irrigation","pos",92),("Température","pos",81),("Humidité","pos",76),
                 ("Pluviométrie","pos",60),("Engrais N","pos",44),("pH sol","neg",35),("Vent","neg",15)],
    "Manioc":   [("Température","pos",84),("Humidité","pos",70),("Pluviométrie","pos",65),
                 ("Engrais N","pos",40),("pH sol","pos",35),("Irrigation","neg",18),("Vent","neg",10)],
    "Mangue":   [("Température","pos",88),("Humidité","pos",75),("Irrigation","pos",60),
                 ("Pluviométrie","pos",55),("pH sol","pos",38),("Engrais N","pos",28),("Vent","neg",12)],
    "Sorgho":   [("Température","pos",80),("Engrais N","pos",65),("Pluviométrie","pos",50),
                 ("Humidité","pos",42),("pH sol","pos",35),("Irrigation","pos",28),("Vent","neg",15)],
    "Arachide": [("Humidité","pos",72),("Température","pos",68),("Pluviométrie","pos",60),
                 ("Engrais N","pos",45),("pH sol","pos",38),("Irrigation","pos",30),("Vent","neg",10)],
    "Orange":   [("Température","pos",82),("Humidité","pos",70),("Irrigation","pos",65),
                 ("Pluviométrie","pos",50),("pH sol","neg",35),("Engrais N","pos",30),("Vent","neg",12)],
}

SHAP_REASONS: dict[str, str] = {
    "Blé":      "La **température optimale (15–20°C)** est le premier levier. L'engrais azoté booste la protéine du grain. Un excès d'humidité pénalise via la verse et les maladies fongiques.",
    "Maïs":     "L'**azote est le facteur limitant principal**. L'irrigation en phase floraison est déterminante. Température et photopériode restent favorables.",
    "Soja":     "Très sensible au **stress hydrique** : humidité et pluviométrie dominent. pH élevé réduit la disponibilité du fer. Peu gourmand en N grâce à la fixation biologique.",
    "Riz":      "Culture **aquatique par excellence** : l'irrigation explique 92% de la variance. La chaleur humide est idéale. Le vent au stade épiaison est le risque négatif principal.",
    "Manioc":   "Très **tolérant à la chaleur** et à la sécheresse modérée. La température et l'humidité ambiante sont les moteurs. Peu exigeant en intrants.",
    "Mangue":   "La **chaleur tropicale (25–35°C)** est le facteur dominant. L'humidité et une irrigation maîtrisée permettent de maximiser la nouaison et la qualité des fruits.",
    "Sorgho":   "Céréale **xérophile** : parfaitement adaptée à la chaleur sèche. L'azote est le second levier après la température. Résistant à la sécheresse légère.",
    "Arachide": "Culture **légumineuse fixatrice d'azote**. L'humidité du sol et la température chaude sont les moteurs principaux. Le drainage est crucial pour éviter la pourriture.",
    "Orange":   "Agrume **sensible à la température** et aux excès d'eau. L'irrigation goutte-à-goutte optimise la qualité. Un pH trop acide réduit l'absorption du calcium.",
}
# Alias rétrocompatible
SHAP_REAS_REASONS = SHAP_REASONS

SHAP_SCORES: dict[str, int] = {
    "Blé":82, "Maïs":91, "Soja":87, "Riz":94,
    "Manioc":79, "Mangue":76, "Sorgho":83, "Arachide":80, "Orange":77,
}

# ── CSS global ────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Tokens ── */
:root {
    --bg: #F0EDE6;
    --surface: #FAFAF7;
    --surface2: #F2EFE8;
    --surface3: #EAE6DC;
    --border: rgba(60,55,40,0.15);
    --border-mid: rgba(60,55,40,0.25);
    --border-strong: rgba(60,55,40,0.40);

    --forest: #1A3528;
    --forest-light: #3D7A55;
    --leaf: #4A7C59;
    --sage: #7FAF8A;
    --lime: #B3D98F;
    --terra: #C05A2E;
    --terra-light: #D4785A;
    --amber: #D4941A;
    --blue: #378ADD;
    --red: #E24B4A;

    --ink: #111111;
    --muted: #444440;
    --caption: #77736C;
    --placeholder: #A09C94;

    --radius: 14px;
    --radius-sm: 8px;
    --radius-xs: 5px;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.10), 0 3px 8px rgba(0,0,0,0.06);

    --transition: 0.18s cubic-bezier(0.4,0,0.2,1);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    color: var(--ink) !important;
}
.stApp {
    background-color: var(--bg) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(170deg, #1A3528 0%, #142B20 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.92) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] label {
    font-size: 10px !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    color: var(--sage) !important;
    font-weight: 700 !important;
    margin-bottom: 5px !important;
}
[data-testid="stSidebar"] .stTextInput input {
    background: #243F30 !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: var(--radius-sm) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
    font-size: 13px !important;
    transition: border-color var(--transition), background var(--transition) !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
    background: #2C4F38 !important;
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 3px rgba(127,175,138,0.22) !important;
    outline: none !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder {
    color: rgba(255,255,255,0.38) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.38) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stDateInput > div > div {
    background: #243F30 !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: var(--radius-sm) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 13px !important;
    transition: border-color var(--transition) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:hover,
[data-testid="stSidebar"] .stDateInput > div > div:hover {
    border-color: var(--sage) !important;
}
[data-testid="stSidebar"] .stSelectbox svg,
[data-testid="stSidebar"] .stDateInput svg {
    fill: rgba(255,255,255,0.60) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, var(--terra) 0%, #A84B24 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 11px 16px !important;
    width: 100% !important;
    box-shadow: 0 2px 8px rgba(192,90,46,0.35) !important;
    transition: all var(--transition) !important;
    letter-spacing: 0.3px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, var(--terra-light) 0%, var(--terra) 100%) !important;
    box-shadow: 0 4px 14px rgba(192,90,46,0.45) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, var(--forest) 0%, #243F30 60%, #1E4830 100%);
    border-radius: 18px;
    padding: 36px 44px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(127,175,138,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 300px; height: 150px;
    background: radial-gradient(ellipse, rgba(179,217,143,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-eyebrow {
    font-size: 10px;
    letter-spacing: 3.5px;
    text-transform: uppercase;
    color: var(--sage);
    margin-bottom: 10px;
    font-weight: 700;
}
.hero-title {
    font-family: 'DM Serif Display', serif !important;
    font-size: 40px !important;
    font-weight: 400 !important;
    color: white !important;
    line-height: 1.12 !important;
    margin: 0 0 10px !important;
}
.hero-title em {
    font-style: italic;
    color: var(--sage) !important;
}
.hero-sub {
    color: rgba(255,255,255,0.78) !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    font-weight: 400 !important;
    max-width: 560px;
}
.hero-chips {
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
    margin-top: 18px;
}
.hero-chip {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 20px;
    padding: 4px 13px;
    font-size: 11px;
    color: rgba(255,255,255,0.85) !important;
    transition: background var(--transition), border-color var(--transition);
}
.hero-chip:hover {
    background: rgba(255,255,255,0.16);
    border-color: rgba(255,255,255,0.28);
}

/* ── Typographie sections ── */
.section-header {
    font-family: 'DM Serif Display', serif !important;
    font-size: 22px !important;
    font-weight: 400 !important;
    color: var(--forest) !important;
    margin: 24px 0 4px !important;
}
.section-sub {
    font-size: 13px !important;
    color: var(--caption) !important;
    margin-bottom: 16px !important;
    line-height: 1.55 !important;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border-mid);
    overflow: hidden;
    margin-bottom: 14px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition), transform var(--transition);
}
.card:hover {
    box-shadow: var(--shadow-md);
}
.card-head {
    padding: 13px 18px 11px;
    border-bottom: 1px solid var(--border);
    background: var(--surface2);
}
.card-title {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: var(--forest) !important;
    margin: 0 !important;
    letter-spacing: 0.2px !important;
}
.card-body {
    padding: 14px 18px;
}

/* ── Data rows ── */
.data-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    transition: background var(--transition);
}
.data-row:last-child { border-bottom: none; }
.data-row:hover { background: var(--surface2); margin: 0 -18px; padding: 8px 18px; }
.data-label { color: var(--caption); font-weight: 600; }
.data-val { font-weight: 600; color: var(--ink); }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-mid) !important;
    border-left: 3px solid var(--leaf) !important;
    padding: 16px 18px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow var(--transition) !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: var(--caption) !important;
    font-weight: 700 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Serif Display', serif !important;
    font-size: 26px !important;
    color: var(--forest) !important;
    font-weight: 400 !important;
}
[data-testid="stMetricDelta"] { font-size: 12px !important; font-weight: 600 !important; }

/* ── Status banners ── */
.status {
    border-radius: var(--radius);
    padding: 13px 16px;
    margin: 10px 0;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    box-shadow: var(--shadow-sm);
}
.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
}
.status-success { background: rgba(61,122,85,0.07); border: 1px solid rgba(61,122,85,0.30); }
.status-success .status-dot { background: var(--forest-light); box-shadow: 0 0 0 3px rgba(61,122,85,0.18); }
.status-success h4 { color: var(--forest-light) !important; }
.status-warning { background: rgba(212,148,26,0.07); border: 1px solid rgba(212,148,26,0.30); }
.status-warning .status-dot { background: var(--amber); box-shadow: 0 0 0 3px rgba(212,148,26,0.18); }
.status-warning h4 { color: #8A5C10 !important; }
.status-danger  { background: rgba(192,90,46,0.07); border: 1px solid rgba(192,90,46,0.30); }
.status-danger .status-dot { background: var(--terra); box-shadow: 0 0 0 3px rgba(192,90,46,0.18); }
.status-danger h4 { color: var(--terra) !important; }
.status h4 { font-size: 13px !important; font-weight: 700 !important; margin: 0 0 3px !important; }
.status p  { font-size: 13px !important; color: var(--muted) !important; margin: 0 !important; line-height: 1.6 !important; }

/* ── Interpret box ── */
.interpret-box {
    background: linear-gradient(135deg, var(--forest) 0%, #243F30 100%);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin: 14px 0;
    box-shadow: var(--shadow-md);
    position: relative;
    overflow: hidden;
}
.interpret-box::before {
    content: '';
    position: absolute;
    top: -30px; right: -30px;
    width: 120px; height: 120px;
    background: radial-gradient(circle, rgba(127,175,138,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.interpret-box-label {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--sage);
    margin-bottom: 8px;
    font-weight: 700;
}
.interpret-box p {
    color: rgba(255,255,255,0.86) !important;
    font-size: 14px !important;
    line-height: 1.78 !important;
    margin: 0 !important;
}
.interpret-box strong { color: var(--sage) !important; font-weight: 700 !important; }

/* ── Chips & Pills ── */
.meta-chip {
    display: inline-flex;
    background: var(--surface2);
    border: 1px solid var(--border-mid);
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 12px;
    font-weight: 600;
    color: var(--ink) !important;
    margin: 2px;
    transition: background var(--transition);
}
.meta-chip:hover { background: var(--surface3); }

.city-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(107,158,120,0.20);
    border: 1px solid rgba(107,158,120,0.40);
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 12px;
    color: var(--sage) !important;
    margin-bottom: 10px;
    font-weight: 600 !important;
}
.city-pill-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--sage);
    flex-shrink: 0;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.6; transform: scale(0.8); }
}

/* ── Sidebar logo ── */
.sidebar-logo {
    text-align: center;
    padding: 20px 0 20px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 18px;
}
.sidebar-logo-name {
    font-family: 'DM Serif Display', serif !important;
    font-size: 20px !important;
    color: white !important;
    margin-top: 10px !important;
    font-weight: 400 !important;
    letter-spacing: 0.3px !important;
}
.sidebar-logo-name em { font-style: italic; color: var(--sage) !important; }
.sidebar-logo-tagline {
    font-size: 10px !important;
    color: rgba(168,196,162,0.65) !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    margin-top: 4px !important;
    font-weight: 700 !important;
}
.sidebar-section {
    border-top: 1px solid rgba(255,255,255,0.10);
    margin: 16px 0 12px;
    padding-top: 14px;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    border: 1px solid var(--border-mid) !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--caption) !important;
    padding: 7px 16px !important;
    border: none !important;
    transition: color var(--transition) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--forest) !important;
    border: 1px solid var(--border-mid) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-mid) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border-mid) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--forest) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all var(--transition) !important;
}
.stDownloadButton > button:hover {
    background: var(--surface2) !important;
    border-color: var(--border-strong) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Toast / notification ── */
.agri-toast {
    position: fixed;
    bottom: 24px; right: 24px;
    background: var(--forest);
    color: white !important;
    padding: 12px 20px;
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--sage);
    font-size: 13px;
    font-weight: 600;
    box-shadow: var(--shadow-lg);
    z-index: 9999;
    animation: slide-in 0.25s ease-out;
}
@keyframes slide-in {
    from { transform: translateX(120%); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
}

/* ── Skeleton loader ── */
.skeleton {
    background: linear-gradient(90deg, var(--surface2) 25%, var(--surface3) 50%, var(--surface2) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    border-radius: var(--radius-sm);
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* ── Progress bar ── */
.agri-progress-wrap {
    background: var(--surface2);
    border-radius: 99px;
    height: 6px;
    overflow: hidden;
    margin: 4px 0;
}
.agri-progress-bar {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--leaf), var(--sage));
    transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
}

/* ── Divider ── */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-mid), transparent);
    border: none;
    margin: 24px 0;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 22px 0 10px;
    font-size: 11px;
    color: var(--caption) !important;
    letter-spacing: 0.3px;
}
.footer span { color: var(--leaf) !important; font-weight: 700 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface2); }
::-webkit-scrollbar-thumb { background: var(--sage); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--leaf); }

/* ── Selection ── */
::selection { background: rgba(61,122,85,0.20); color: var(--forest); }

/* ── Badge live (hero) ── */
.badge-live {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(61,122,85,0.28);
    border: 1px solid rgba(127,175,138,0.38);
    border-radius: 20px;
    padding: 4px 11px;
    font-size: 10px;
    font-weight: 700;
    color: var(--sage) !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.badge-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--sage);
    flex-shrink: 0;
    animation: blink-dot 2s infinite;
}
@keyframes blink-dot {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.3; }
}

/* ── Hero — ligne de séparation ── */
.divider-line {
    width: 44px;
    height: 2px;
    background: var(--leaf);
    border-radius: 2px;
    margin: 0 0 18px;
}

/* ── Hero — stats ── */
.hero-stats {
    display: flex;
    gap: 24px;
    margin-bottom: 22px;
    flex-wrap: wrap;
    align-items: center;
}
.hero-stat {
    display: flex;
    flex-direction: column;
    gap: 3px;
}
.hero-stat-val {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    font-weight: 400;
    color: #fff;
    line-height: 1;
}
.hero-stat-val em { font-style: italic; color: var(--lime); }
.hero-stat-label {
    font-size: 11px;
    color: rgba(255,255,255,0.42);
    font-weight: 500;
    letter-spacing: 0.4px;
}
.hero-stat-sep {
    width: 1px;
    background: rgba(255,255,255,0.14);
    align-self: stretch;
    min-height: 28px;
}

/* ── Hero — chip accent ── */
.hero-chip-accent {
    background: rgba(61,122,85,0.32) !important;
    border-color: rgba(127,175,138,0.42) !important;
    color: var(--lime) !important;
}

/* ── Module cards ── */
.mod-card {
    background: var(--surface);
    border: 1px solid var(--border-mid);
    border-radius: var(--radius);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition), border-color var(--transition);
    height: 100%;
}
.mod-card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--border-strong);
}
.mod-icon {
    width: 36px; height: 36px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}
.mod-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 700;
    margin: 0;
}
.mod-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--forest);
    line-height: 1.3;
    margin: 0;
}
.mod-desc {
    font-size: 12px;
    color: var(--caption);
    line-height: 1.55;
    margin: 0;
    flex: 1;
}
</style>
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Couche réseau — avec retries + circuit-breaker léger
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class APIError(Exception):
    """Erreur réseau ou serveur AgriSim."""

def _api_get(path: str, **kwargs) -> requests.Response:
    """GET avec retries exponentiels."""
    url = f"{CONFIG.api_url}{path}"
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(CONFIG.request_retries + 1):
        try:
            r = requests.get(url, timeout=CONFIG.api_timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < CONFIG.request_retries:
                time.sleep(CONFIG.request_backoff * (2 ** attempt))
    raise APIError(f"GET {path} a échoué après {CONFIG.request_retries + 1} tentatives : {last_exc}") from last_exc

def _api_post(path: str, **kwargs) -> requests.Response:
    """POST avec retries exponentiels."""
    url = f"{CONFIG.api_url}{path}"
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(CONFIG.request_retries + 1):
        try:
            r = requests.post(url, timeout=CONFIG.api_timeout, **kwargs)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < CONFIG.request_retries:
                time.sleep(CONFIG.request_backoff * (2 ** attempt))
    raise APIError(f"POST {path} a échoué après {CONFIG.request_retries + 1} tentatives : {last_exc}") from last_exc

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fonctions de données
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=CONFIG.history_ttl, show_spinner=False)
def load_history() -> pd.DataFrame:
    """Charge l'historique des prédictions depuis l'API."""
    try:
        r = _api_get("/history")
        data = r.json()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["date_prediction"] = pd.to_datetime(df["date_prediction"])
        return df.sort_values("date_prediction").reset_index(drop=True)
    except APIError as e:
        logger.warning("load_history : %s", e)
    except Exception as e:
        logger.exception("load_history inattendu : %s", e)
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_cultures() -> list[str]:
    """Charge la liste des cultures depuis le CSV local, avec fallback hardcodé."""
    _FALLBACK = [
        "Blé","Maïs","Riz (paddy)","Soja","Orge","Coton",
        "Manioc","Mangue","Sorgho","Arachide","Orange",
    ]
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "backend", "data", "cultures_agricoles.csv"
    )
    try:
        df = pd.read_csv(csv_path)
        cultures = df["Culture"].dropna().unique().tolist()
        return sorted(cultures) if cultures else _FALLBACK
    except FileNotFoundError:
        logger.warning("cultures_agricoles.csv introuvable, utilisation du fallback.")
    except Exception as e:
        logger.exception("load_cultures inattendu : %s", e)
    return _FALLBACK


@st.cache_data(ttl=300, show_spinner=False)
def search_city(query: str) -> list[dict]:
    """Recherche une ville via l'API. Résultats mis en cache 5 min."""
    if not query or len(query.strip()) < 2:
        return []
    try:
        r = _api_post("/cities/search", json={"query": query.strip()})
        return r.json() or []
    except APIError as e:
        logger.warning("search_city('%s') : %s", query, e)
    return []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers graphiques
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chart_layout(**overrides):
    layout = CHART_LAYOUT.copy()
    layout.update(overrides)
    return layout


def empty_fig(msg: str = "Données insuffisantes", h: int = 220) -> go.Figure:
    fig = go.Figure()

    fig.add_annotation(
        text=msg,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=13, color=PAL.caption, family="Outfit"),
    )

    fig.update_layout(
        **chart_layout(
            height=h,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
    )

    return fig


def progress_bar_html(value: float, max_value: float = 100, color: Optional[str] = None) -> str:
    """Retourne le HTML d'une barre de progression stylisée (0–max_value)."""
    pct = max(0.0, min(100.0, value / max_value * 100))
    col = color or PAL.leaf
    return (
        f'<div class="agri-progress-wrap">'
        f'<div class="agri-progress-bar" style="width:{pct:.1f}%;background:{col};"></div>'
        f'</div>'
    )


def status_html(level: str, title: str, body: str) -> str:
    """Génère un bandeau status (success | warning | danger)."""
    level = level if level in ("success", "warning", "danger") else "success"
    return (
        f'<div class="status status-{level}">'
        f'<div class="status-dot"></div>'
        f'<div><h4>{title}</h4><p>{body}</p></div>'
        f'</div>'
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Composants UI Streamlit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@lru_cache(maxsize=1)
def _logo_b64() -> Optional[str]:
    """Encode le logo en base64 (mis en cache pour la durée du process)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def sidebar_logo() -> None:
    """Affiche le logo AgriSim AI dans la sidebar."""
    b64 = _logo_b64()
    if b64:
        img_html = (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="border-radius:50%;width:72px;border:2px solid rgba(255,255,255,0.25);" />'
        )
    else:
        img_html = (
            '<img src="https://images.unsplash.com/photo-1625246333195-7e99cabd36dc'
            '?auto=format&fit=crop&w=120&h=120&q=80" '
            'style="border-radius:50%;width:72px;border:2px solid rgba(255,255,255,0.25);" />'
        )
    st.markdown(
        f"""
        <div class="sidebar-logo">
            <div style="text-align:center;margin-bottom:10px;">{img_html}</div>
            <div class="sidebar-logo-name">AgriSim <em>AI</em></div>
            <div class="sidebar-logo-tagline">Simulation agricole</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_location() -> dict:
    """
    Bloc localisation dans la sidebar.

    Returns
    -------
    dict avec les clés : zone, country, admin1, latitude, longitude
    ou dict vide si aucune ville sélectionnée.
    """
    st.markdown("**Localisation**")
    city_query = st.text_input(
        "Rechercher une ville", "Paris",
        key="city_input",
        placeholder="Ex : Dakar, Lyon…",
    )
    cities = search_city(city_query) if city_query else []

    if not cities:
        if city_query:
            st.markdown(
                '<p style="font-size:12px;color:rgba(255,255,255,0.45);margin-top:4px;">'
                'Aucune ville trouvée.</p>',
                unsafe_allow_html=True,
            )
        return {}

    opts = [f"{c['name']} — {c.get('admin1','')} · {c['country']}" for c in cities]
    label = st.selectbox("Ville proposée", opts, key="city_select")
    sel   = cities[opts.index(label)]

    st.markdown(
        f'<div class="city-pill">'
        f'<div class="city-pill-dot"></div>'
        f'{sel["name"]}, {sel.get("admin1","")}, {sel.get("country","")}'
        f'</div>',
        unsafe_allow_html=True,
    )
    return {
        "zone":      sel["name"],
        "country":   sel.get("country", ""),
        "admin1":    sel.get("admin1", ""),
        "latitude":  sel["latitude"],
        "longitude": sel["longitude"],
    }


def footer(
    author: str = "Lallene &amp; Associés (Expertise SSI &amp; Systèmes)",
    links: list[tuple[str, str]] | None = None,
) -> None:
    """
    Affiche le pied de page fixe AgriSim AI.

    Parameters
    ----------
    author : mention auteur affichée au centre
    links  : liste de (label, href) pour les liens. Par défaut : Documentation, Performances ML, Support.
    """
    if links is None:
        links = [
            ("Documentation",    "#"),
            ("Performances ML",  "pages/5_Performances_ML.py"),
            ("Support",          "#"),
        ]

    links_html = " &nbsp;·&nbsp; ".join(
        f'<a class="footer-link" href="{href}">{label}</a>'
        for label, href in links
    )

    st.markdown(f"""
    <style>
    .agri-footer {{
        position: fixed;
        left: 0; bottom: 0;
        width: 100%;
        background: linear-gradient(180deg, rgba(240,237,230,0) 0%, #F0EDE6 18%);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        text-align: center;
        padding: 10px 16px 12px;
        font-size: 11px;
        font-family: 'Outfit', sans-serif;
        border-top: 1px solid rgba(60,55,40,0.12);
        z-index: 999;
        color: #77736C;
        line-height: 1.6;
    }}
    .agri-footer strong {{ color: #111; font-weight: 600; }}
    .agri-footer .footer-brand {{ color: #3D7A55; font-weight: 700; }}
    .agri-footer-links {{ margin-top: 3px; }}
    .agri-footer .footer-link {{
        color: #3D7A55;
        text-decoration: none;
        font-weight: 600;
        transition: color 0.15s;
    }}
    .agri-footer .footer-link:hover {{ color: #1A3528; text-decoration: underline; }}
    .agri-footer .footer-dot {{ color: rgba(100,100,100,0.35); margin: 0 2px; }}
    </style>
    <div class="agri-footer">
        <div>
            AgriSim <span class="footer-brand">AI</span>
            <span class="footer-dot">&nbsp;·&nbsp;</span>
            Simulation agricole intelligente
            <span class="footer-dot">&nbsp;·&nbsp;</span>
            {author}
            <span class="footer-dot">&nbsp;·&nbsp;</span>
            FastAPI &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Scikit-learn
        </div>
        <div class="agri-footer-links">{links_html}</div>
    </div>
    <div style="height:56px;"></div>
    """, unsafe_allow_html=True)


def show_api_error(message: str = "Impossible de joindre le serveur.") -> None:
    """Affiche un bandeau d'erreur API unifié."""
    st.markdown(
        status_html("danger", "Erreur de connexion", message),
        unsafe_allow_html=True,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Composants de page — hero & modules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def hero_html(
    eyebrow: str = "Plateforme de simulation",
    title: str = "AgriSim",
    title_em: str = "AI",
    subtitle: str = (
        "Transformez vos données météo, sols et pratiques culturales en prédictions "
        "de rendement fiables — via apprentissage automatique et interprétabilité SHAP."
    ),
    stats: list[tuple[str, str, str]] | None = None,
    chips: list[str] | None = None,
    chips_accent: list[str] | None = None,
    badge_label: str = "Intelligence agricole",
) -> str:
    """
    Retourne le HTML du bloc hero AgriSim.

    Parameters
    ----------
    eyebrow        : texte au-dessus du titre (uppercase)
    title          : partie normale du titre
    title_em       : partie italique du titre (en vert)
    subtitle       : texte descriptif
    stats          : liste de (valeur, unité_em, label) — ex: [("20+","cultures","supportées")]
    chips          : liste de tags neutres
    chips_accent   : liste de tags mis en avant (vert)
    badge_label    : texte du badge animé en haut à gauche

    Usage
    -----
    st.markdown(hero_html(), unsafe_allow_html=True)
    """
    if stats is None:
        stats = [
            ("20+",  "cultures", "supportées"),
            ("94", "%",        "précision modèle"),
            ("7",  "facteurs", "analysés par SHAP"),
        ]
    if chips is None:
        chips = ["FastAPI", "Streamlit", "APIs Météo"]
    if chips_accent is None:
        chips_accent = ["Machine Learning", "SHAP"]

    # Stats HTML
    stats_parts: list[str] = []
    for i, (val, em, label) in enumerate(stats):
        if i > 0:
            stats_parts.append('<div class="hero-stat-sep"></div>')
        stats_parts.append(
            f'<div class="hero-stat">'
            f'<span class="hero-stat-val">{val} <em>{em}</em></span>'
            f'<span class="hero-stat-label">{label}</span>'
            f'</div>'
        )
    stats_html = "\n".join(stats_parts)

    # Chips HTML
    chips_html_parts = [
        f'<span class="hero-chip hero-chip-accent">{c}</span>' for c in chips_accent
    ] + [
        f'<span class="hero-chip">{c}</span>' for c in chips
    ]
    chips_html = "\n".join(chips_html_parts)

    return f"""
<div class="hero">
  <div class="badge-live"><div class="badge-dot"></div>{badge_label}</div>
  <p class="hero-eyebrow">{eyebrow}</p>
  <h1 class="hero-title">{title} <em>{title_em}</em></h1>
  <div class="divider-line"></div>
  <p class="hero-sub">{subtitle}</p>
  <div class="hero-stats">{stats_html}</div>
  <div class="hero-chips">{chips_html}</div>
</div>
"""


# Configuration des modules de navigation
# Chaque entrée : (page, icone, label_catégorie, bg_icone, couleur_label, titre, description)
NAV_MODULES: list[tuple[str, str, str, str, str, str, str]] = [
    (
        "pages/1_Dashboard.py",
        "📊", "Analytique", "#EAF3DE", "#3B6D11",
        "Dashboard",
        "Heatmap rendement, évolution temporelle, top cultures et corrélations.",
    ),
    (
        "pages/2_Prediction.py",
        "🌱", "Simulation", "#E1F5EE", "#0F6E56",
        "Prédiction",
        "Simulez le rendement selon zone, engrais, irrigation et période.",
    ),
    (
        "pages/4_IA_Explicable.py",
        "🔍", "Explicabilité", "#FAEEDA", "#854F0B",
        "IA Explicable",
        "SHAP : importance des features, radar et explication par culture.",
    ),
    (
        "pages/3_Historique.py",
        "📋", "Données", "#E6F1FB", "#185FA5",
        "Historique",
        "Consultez, filtrez et exportez toutes les prédictions enregistrées.",
    ),
    (
        "pages/5_Performances_ML.py",
        "⚙️", "Évaluation", "#FAECE7", "#993C1D",
        "Performances ML",
        "Comparaison R², MAE, RMSE et violin plots par culture.",
    ),
]


def modules_html(modules: list[tuple] | None = None) -> str:
    """
    Retourne le HTML des cartes de navigation des modules (sans les boutons Streamlit).
    À combiner avec des `st.button` / `st.switch_page` pour la navigation réelle.

    Parameters
    ----------
    modules : liste de tuples (page, icone, label, bg, fg, titre, desc).
              Par défaut, utilise NAV_MODULES.

    Usage
    -----
    st.markdown(modules_html(), unsafe_allow_html=True)
    """
    if modules is None:
        modules = NAV_MODULES

    cards = []
    for _, icon, label, bg, fg, title, desc in modules:
        cards.append(f"""
  <div class="mod-card">
    <div class="mod-icon" style="background:{bg};">{icon}</div>
    <p class="mod-label" style="color:{fg};">{label}</p>
    <p class="mod-title">{title}</p>
    <p class="mod-desc">{desc}</p>
  </div>""")

    cards_html = "\n".join(cards)
    return f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">{cards_html}\n</div>'


def render_modules(modules: list[tuple] | None = None, n_cols: int = 3) -> None:
    """
    Affiche les cartes modules avec navigation Streamlit fonctionnelle.

    Chaque carte est rendue en HTML (visuel) + un bouton st.button transparent
    superposé via une colonne Streamlit.

    Parameters
    ----------
    modules : liste de tuples — par défaut NAV_MODULES
    n_cols  : nombre de colonnes (2 ou 3)

    Usage
    -----
    render_modules()          # grille 3 colonnes par défaut
    render_modules(n_cols=2)  # grille 2 colonnes
    """
    if modules is None:
        modules = NAV_MODULES

    cols = st.columns(n_cols, gap="medium")
    for i, (page, icon, label, bg, fg, title, desc) in enumerate(modules):
        with cols[i % n_cols]:
            st.markdown(f"""
            <div class="mod-card">
              <div class="mod-icon" style="background:{bg};">{icon}</div>
              <p class="mod-label" style="color:{fg};">{label}</p>
              <p class="mod-title">{title}</p>
              <p class="mod-desc">{desc}</p>
            </div>""", unsafe_allow_html=True)
            if st.button("Ouvrir →", key=f"mod_{i}", use_container_width=True):
                st.switch_page(page)