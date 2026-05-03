import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, PAL, CHART_COLORS, CHART_LAYOUT, sidebar_logo, load_history, footer

# Redéfinition du dictionnaire pour éviter l'erreur TypeError
PAL = {
    "forest": "#1A3528", "leaf":  "#3D7A55", "sage":  "#7FAF8A",
    "lime":   "#B3D98F", "terra": "#C05A2E", "amber": "#EF9F27",
    "blue":   "#378ADD", "red":   "#E24B4A",
}

st.set_page_config(page_title="Performances ML — AgriSim AI", page_icon="⚙️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    sidebar_logo()
    st.page_link("app.py",                     label="🏠  Accueil")
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard")
    st.page_link("pages/2_Prediction.py",      label="🌱  Prédiction")
    st.page_link("pages/3_Historique.py",      label="📋  Historique")
    st.page_link("pages/4_IA_Explicable.py",   label="🔍  IA Explicable")
    st.page_link("pages/5_Performances_ML.py", label="⚙️  Performances ML")

st.markdown('<div class="section-header">Comparaison des modèles ML</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Évaluation des modèles selon les métriques standards : MAE, RMSE et R².</p>', unsafe_allow_html=True)

# ── Chargement résultats ML ────────────────────────────────────
try:
    df_ml = pd.read_csv("../backend/model/model_results.csv")
    st.dataframe(df_ml, use_container_width=True)
    st.download_button(
        "Télécharger les performances ML (CSV)",
        data=df_ml.to_csv(index=False).encode("utf-8"),
        file_name="performances_modeles.csv", mime="text/csv",
        use_container_width=True,
    )
    models_df = df_ml
except Exception:
    st.info("Fichier model_v5_results.csv introuvable — affichage des données de démonstration.")
    models_df = pd.DataFrame({
        "Modèle": ["Random Forest","XGBoost","Ridge","SVR"],
        "R2":     [0.94, 0.92, 0.85, 0.88],
        "MAE":    [0.31, 0.36, 0.54, 0.44],
        "RMSE":   [0.42, 0.48, 0.67, 0.55],
    })

# ── Graphiques R² + MAE ────────────────────────────────────────
if {"Modèle","R2","MAE"}.issubset(models_df.columns):
    names   = models_df["Modèle"].tolist()
    bcolors = [CHART_COLORS[i%len(CHART_COLORS)] for i in range(len(names))]

    col_r2, col_mae = st.columns(2, gap="large")
    with col_r2:
        fig_r2 = go.Figure(go.Bar(
            x=names, y=models_df["R2"],
            marker_color=bcolors,
            text=[f"{v:.3f}" for v in models_df["R2"]],
            textposition="outside", textfont=dict(size=11),
        ))
        fig_r2.update_layout(
            title=dict(text="R² par modèle", font=dict(size=14,family="DM Serif Display")),
            height=280, **CHART_LAYOUT,
            yaxis=dict(range=[0,1.08], gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        )
        st.plotly_chart(fig_r2, use_container_width=True)

    with col_mae:
        fig_mae = go.Figure(go.Bar(
            x=names, y=models_df["MAE"],
            marker_color=bcolors,
            text=[f"{v:.3f}" for v in models_df["MAE"]],
            textposition="outside", textfont=dict(size=11),
        ))
        fig_mae.update_layout(
            title=dict(text="MAE par modèle", font=dict(size=14,family="DM Serif Display")),
            height=280, **CHART_LAYOUT,
            yaxis=dict(gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        )
        st.plotly_chart(fig_mae, use_container_width=True)

    if "RMSE" in models_df.columns:
        st.markdown('<div class="section-header">RMSE par modèle</div>', unsafe_allow_html=True)
        fig_rmse = go.Figure(go.Bar(
            x=names, y=models_df["RMSE"],
            marker_color=bcolors,
            text=[f"{v:.3f}" for v in models_df["RMSE"]],
            textposition="outside", textfont=dict(size=11),
        ))
        fig_rmse.update_layout(
            height=260, **CHART_LAYOUT,
            yaxis=dict(gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        )
        st.plotly_chart(fig_rmse, use_container_width=True)

# ── Analyse des prédictions réelles ───────────────────────────
df_hist = load_history()

if not df_hist.empty:
    st.markdown('<hr class="fancy-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Analyse des prédictions réelles</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Distribution et variabilité des rendements prédits depuis la base de données.</p>', unsafe_allow_html=True)

    # Violin plots
    fig_v = go.Figure()
    for i, cult in enumerate(df_hist["culture"].unique()):
        sub = df_hist[df_hist["culture"]==cult]["rendement_predit"]
        if len(sub) >= 2:
            fig_v.add_trace(go.Violin(
                y=sub, name=cult,
                fillcolor=CHART_COLORS[i%len(CHART_COLORS)],
                line_color="#1A3528", opacity=0.75,
                box_visible=True, meanline_visible=True,
                hovertemplate=f"<b>{cult}</b><br>%{{y:.2f}} t/ha<extra></extra>",
            ))
    if fig_v.data:
        fig_v.update_layout(
            height=320, **CHART_LAYOUT,
            yaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
            xaxis=dict(tickfont=dict(size=11)),
            legend=dict(orientation="h", y=-0.22, font=dict(size=11)),
            violingap=0.3, violinmode="group",
        )
        st.plotly_chart(fig_v, use_container_width=True)

    # Tableau statistiques par culture
    st.markdown('<div class="section-header">Statistiques par culture</div>', unsafe_allow_html=True)
    stats = (df_hist.groupby("culture")["rendement_predit"]
             .agg(["count","mean","min","max","std"])
             .round(2)
             .reset_index())
    stats.columns = ["Culture","Observations","Moyenne","Min","Max","Écart-type"]
    st.dataframe(stats, use_container_width=True, hide_index=True)

    # Histogramme global
    st.markdown('<div class="section-header">Distribution globale des rendements</div>', unsafe_allow_html=True)
    fig_hist_dist = go.Figure(go.Histogram(
        x=df_hist["rendement_predit"],
        nbinsx=20,
        marker_color="#3D7A55",
        opacity=0.85,
        hovertemplate="Rendement : %{x:.2f} t/ha<br>Fréquence : %{y}<extra></extra>",
    ))
    fig_hist_dist.update_layout(
        height=260, **CHART_LAYOUT,
        xaxis=dict(title="Rendement prédit (t/ha)", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        yaxis=dict(title="Fréquence", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        bargap=0.05,
    )
    st.plotly_chart(fig_hist_dist, use_container_width=True)

footer()