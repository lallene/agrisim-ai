import streamlit as st
from utils import CSS, sidebar_logo, footer, hero_html, render_modules
import os

# Récupération dynamique du chemin du fichier .ico (dans le dossier racine, au même niveau que utils.py)
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
favicon_path = os.path.join(current_dir, "agrisim_ai_logo.ico")

# Configuration de la page
if os.path.exists(favicon_path):
    st.set_page_config(
        page_title="AgriSim AI",
        page_icon=favicon_path,
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_title="AgriSim AI",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Définition de l'URL de l'API (accessible dans toutes les pages)
API_URL = "http://127.0.0.1:8000"

st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    sidebar_logo()
    st.markdown("""
    <div style="font-size:10px;color:rgba(255,255,255,0.45);letter-spacing:2.5px;
    text-transform:uppercase;font-weight:700;margin-bottom:10px;">Navigation</div>
    """, unsafe_allow_html=True)
    st.page_link("app.py",                     label="🏠  Accueil")
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard")
    st.page_link("pages/2_Prediction.py",      label="🌱  Prédiction")
    st.page_link("pages/3_Historique.py",      label="📋  Historique")
    st.page_link("pages/4_IA_Explicable.py",   label="🔍  IA Explicable")
    st.page_link("pages/5_Performances_ML.py", label="⚙️  Performances ML")

# ── Hero ───────────────────────────────────────────────────────
st.markdown(hero_html(), unsafe_allow_html=True)

# ── Modules ────────────────────────────────────────────────────
st.markdown('<p class="section-header">Modules disponibles</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Sélectionnez un module pour commencer.</p>', unsafe_allow_html=True)

render_modules()

footer()