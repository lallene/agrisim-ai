import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, PAL, CHART_COLORS, CHART_LAYOUT, sidebar_logo, load_history, footer

st.set_page_config(page_title="Historique — AgriSim AI", page_icon="📋", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    sidebar_logo()
    st.page_link("app.py",                     label="🏠  Accueil")
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard")
    st.page_link("pages/2_Prediction.py",      label="🌱  Prédiction")
    st.page_link("pages/3_Historique.py",      label="📋  Historique")
    st.page_link("pages/4_IA_Explicable.py",   label="🔍  IA Explicable")
    st.page_link("pages/5_Performances_ML.py", label="⚙️  Performances ML")
    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    if st.button("🔄  Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown('<div class="section-header">Historique des prédictions</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Consultez, filtrez et exportez l\'ensemble des prédictions enregistrées dans la base de données.</p>', unsafe_allow_html=True)

df = load_history()

if df.empty:
    st.info("Aucune prédiction enregistrée pour le moment.")
    st.stop()

# ── Filtres ────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    f_cult = st.selectbox("Culture", ["Toutes"] + sorted(df["culture"].dropna().unique().tolist()))
with fc2:
    f_zone = st.selectbox("Zone",    ["Toutes"] + sorted(df["zone"].dropna().unique().tolist()))
with fc3:
    f_irr  = st.selectbox("Irrigation", ["Toutes","oui","non"])
with fc4:
    f_sol  = st.selectbox("Type de sol", ["Tous"] + sorted(df["type_sol"].dropna().unique().tolist()) if "type_sol" in df.columns else ["Tous"])

dff = df.copy()
if f_cult != "Toutes": dff = dff[dff["culture"]   == f_cult]
if f_zone != "Toutes": dff = dff[dff["zone"]       == f_zone]
if f_irr  != "Toutes": dff = dff[dff["irrigation"] == f_irr]
if "type_sol" in dff.columns and f_sol != "Tous":
    dff = dff[dff["type_sol"] == f_sol]

if dff.empty:
    st.warning("Aucune donnée ne correspond aux filtres.")
    st.stop()

# ── KPIs filtrés ───────────────────────────────────────────────
k1,k2,k3,k4 = st.columns(4)
k1.metric("Résultats filtrés",   str(len(dff)))
k2.metric("Rendement moyen",     f"{dff['rendement_predit'].mean():.2f} t/ha")
k3.metric("Meilleur rendement",  f"{dff['rendement_predit'].max():.2f} t/ha")
k4.metric("Cultures distinctes", str(dff["culture"].nunique()))
st.markdown("<br>", unsafe_allow_html=True)

# ── Tableau ────────────────────────────────────────────────────
cols_show = [c for c in [
    "id","date_prediction","zone","culture","rendement_predit",
    "temperature","humidite","pluviometrie","engrais","irrigation","type_sol","ph"
] if c in dff.columns]

rename_map = {
    "id":"#","date_prediction":"Date","zone":"Zone","culture":"Culture",
    "rendement_predit":"Rendement (t/ha)","temperature":"Temp. (°C)",
    "humidite":"Humidité (%)","pluviometrie":"Pluie (mm)",
    "engrais":"Engrais (kg/ha)","irrigation":"Irrigation",
    "type_sol":"Sol","ph":"pH"
}
st.dataframe(dff[cols_show].rename(columns=rename_map), use_container_width=True, hide_index=True)

st.download_button(
    "Télécharger l'historique filtré (CSV)",
    data=dff.to_csv(index=False).encode("utf-8"),
    file_name="historique_predictions.csv", mime="text/csv",
    use_container_width=True,
)

# ── Évolution ─────────────────────────────────────────────────
st.markdown('<div class="section-header">Évolution des rendements</div>', unsafe_allow_html=True)
fig_ev = go.Figure()
for i, cult in enumerate(dff["culture"].unique()):
    sub = dff[dff["culture"]==cult].sort_values("date_prediction")
    fig_ev.add_trace(go.Scatter(
        x=sub["date_prediction"], y=sub["rendement_predit"],
        name=cult, mode="lines+markers",
        line=dict(color=CHART_COLORS[i%len(CHART_COLORS)], width=2),
        marker=dict(size=6),
    ))
fig_ev.update_layout(
    height=340, **CHART_LAYOUT,
    legend=dict(orientation="h", y=-0.22, font=dict(size=11)),
    xaxis=dict(showgrid=False, tickfont=dict(size=10), tickformat="%d/%m %H:%M"),
    yaxis=dict(gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10), title="t/ha"),
)
st.plotly_chart(fig_ev, use_container_width=True)

# ── Carte ──────────────────────────────────────────────────────
if "latitude" in dff.columns and "longitude" in dff.columns:
    st.markdown('<div class="section-header">Carte des prédictions</div>', unsafe_allow_html=True)
    st.map(dff.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]].dropna())

footer()