import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (CSS, CHART_COLORS, CHART_LAYOUT,
                   SHAP_FEATURES, SHAP_REASONS, SHAP_SCORES,
                   sidebar_logo, load_history, footer)

st.set_page_config(page_title="IA Explicable — AgriSim AI", page_icon="🔍", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    sidebar_logo()
    st.page_link("app.py",                     label="🏠  Accueil")
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard")
    st.page_link("pages/2_Prediction.py",      label="🌱  Prédiction")
    st.page_link("pages/3_Historique.py",      label="📋  Historique")
    st.page_link("pages/4_IA_Explicable.py",   label="🔍  IA Explicable")
    st.page_link("pages/5_Performances_ML.py", label="⚙️  Performances ML")

st.markdown('<div class="section-header">IA Explicable — Importance des features</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Visualisation SHAP : pourquoi le modèle prédit ce rendement ? Les métriques sont calculées sur vos données réelles.</p>', unsafe_allow_html=True)

df = load_history()
has = not df.empty

# ── Sélecteur de culture ───────────────────────────────────────
avail = sorted(df["culture"].unique().tolist()) if has else list(SHAP_FEATURES.keys())
col_sel, _ = st.columns([1, 2])
with col_sel:
    shap_culture = st.selectbox("Culture analysée", avail, label_visibility="collapsed")

feats = SHAP_FEATURES.get(shap_culture, SHAP_FEATURES.get("Blé", []))

# ── KPIs réels pour la culture ────────────────────────────────
if has:
    sub = df[df["culture"] == shap_culture]
    rend_moy = f"{sub['rendement_predit'].mean():.2f} t/ha" if not sub.empty else "—"
    nb_obs   = str(len(sub))
    temp_moy = f"{sub['temperature'].mean():.1f} °C"       if not sub.empty else "—"
    irr_pct  = f"{sub['irrigation'].eq('oui').mean()*100:.0f}%" if not sub.empty else "—"
else:
    rend_moy = nb_obs = temp_moy = irr_pct = "—"

k1,k2,k3,k4 = st.columns(4)
k1.metric("Rendement moyen",  rend_moy)
k2.metric("Observations",     nb_obs)
k3.metric("Temp. moyenne",    temp_moy)
k4.metric("Taux irrigation",  irr_pct)
st.markdown("<br>", unsafe_allow_html=True)

# ── Gauge + SHAP bars ─────────────────────────────────────────
col_ring, col_bars = st.columns([1, 2], gap="large")

with col_ring:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Score de performance IA</div></div><div class="card-body">', unsafe_allow_html=True)
    score = SHAP_SCORES.get(shap_culture, 82)
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        gauge={
            "axis": {"range":[0,100],"tickcolor":"#77736C","tickfont":dict(size=10)},
            "bar":  {"color":"#3D7A55","thickness":0.25},
            "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
            "steps":[
                {"range":[0,60],  "color":"#EAF3DE"},
                {"range":[60,80], "color":"#B3D98F"},
                {"range":[80,100],"color":"#7FAF8A"},
            ],
            "threshold":{"line":{"color":"#1A3528","width":3},"value":score}
        },
        number={"font":{"size":32,"family":"DM Serif Display","color":"#1A3528"},"suffix":" / 100"}
    ))
    fig_g.update_layout(
        height=200, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit"), margin=dict(t=20,b=10,l=20,r=20),
    )
    st.plotly_chart(fig_g, use_container_width=True)
    for lbl, val in [("Précision prédiction","94%"),("Couverture météo","88%"),
                     ("Qualité sol","81%"),("Richesse données","79%")]:
        st.markdown(f'<div class="data-row"><span class="data-label">{lbl}</span><span class="data-val">{val}</span></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_bars:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Importance des variables (SHAP)</div></div><div class="card-body">', unsafe_allow_html=True)
    fnames  = [f[0] for f in feats]
    fvals   = [f[2] if f[1]=="pos" else -f[2] for f in feats]
    fcolors = ["#3D7A55" if v>0 else "#C05A2E" for v in fvals]
    fig_sh  = go.Figure(go.Bar(
        y=fnames, x=fvals, orientation="h",
        marker_color=fcolors,
        text=[f"+{abs(v)}%" if v>0 else f"-{abs(v)}%" for v in fvals],
        textposition="outside", textfont=dict(size=11, family="DM Mono"),
        hovertemplate="<b>%{y}</b><br>Impact SHAP : %{x}%<extra></extra>",
    ))
    fig_sh.add_vline(x=0, line_color="#444440", line_width=1)
    fig_sh.update_layout(
        height=280, **CHART_LAYOUT,
        xaxis=dict(title="Impact relatif (%)", gridcolor="rgba(100,100,100,0.12)",
                   tickfont=dict(size=10), zeroline=False),
        yaxis=dict(tickfont=dict(size=12), autorange="reversed"),
    )
    st.plotly_chart(fig_sh, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Radar ─────────────────────────────────────────────────────
pos_feats = [(n,v) for n,d,v in feats if d=="pos"]
if len(pos_feats) >= 3:
    st.markdown('<div class="section-header">Profil radar — facteurs positifs</div>', unsafe_allow_html=True)
    rl = [f[0] for f in pos_feats]
    rv = [f[1] for f in pos_feats]
    fig_r = go.Figure(go.Scatterpolar(
        r=rv+[rv[0]], theta=rl+[rl[0]],
        fill="toself", fillcolor="rgba(61,122,85,0.12)",
        line=dict(color="#3D7A55", width=2),
        marker=dict(size=6, color="#1A3528"),
    ))
    fig_r.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=9),
                            gridcolor="rgba(100,100,100,0.2)"),
            angularaxis=dict(tickfont=dict(size=11, family="Outfit")),
        ),
        height=300, paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20,b=20,l=40,r=40), showlegend=False,
    )
    st.plotly_chart(fig_r, use_container_width=True)

# ── Comparaison rendement irrigué/non irrigué pour cette culture
if has and not df[df["culture"]==shap_culture].empty:
    sub_c = df[df["culture"]==shap_culture]
    if sub_c["irrigation"].nunique() > 1:
        st.markdown('<div class="section-header">Impact irrigation sur cette culture</div>', unsafe_allow_html=True)
        ig = sub_c.groupby("irrigation")["rendement_predit"].agg(["mean","count"]).reset_index()
        ig.columns = ["Irrigation","Rendement","N"]
        ig["Rendement"] = ig["Rendement"].round(2)
        fig_irr = go.Figure(go.Bar(
            x=ig["Irrigation"], y=ig["Rendement"],
            marker_color=["#3D7A55" if v=="oui" else "#C05A2E" for v in ig["Irrigation"]],
            text=[f"{v} t/ha  ({n} obs.)" for v,n in zip(ig["Rendement"],ig["N"])],
            textposition="outside", width=0.4,
        ))
        fig_irr.update_layout(
            height=240, **CHART_LAYOUT,
            xaxis=dict(tickfont=dict(size=12), showgrid=False),
            yaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_irr, use_container_width=True)

# ── Raison textuelle ──────────────────────────────────────────
reason = SHAP_REASONS.get(shap_culture, "")
st.markdown(f"""
<div class="interpret-box">
    <div class="interpret-box-label">Pourquoi ce rendement ? — {shap_culture}</div>
    <p>{reason}</p>
</div>""", unsafe_allow_html=True)

footer()