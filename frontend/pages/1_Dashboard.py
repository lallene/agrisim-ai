import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import CSS, PAL, CHART_COLORS, CHART_LAYOUT, sidebar_logo, load_history, empty_fig, footer

st.set_page_config(page_title="Dashboard — AgriSim AI", page_icon="📊", layout="wide")
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

# ── Chargement ─────────────────────────────────────────────────
df = load_history()
has = not df.empty

st.markdown('<div class="section-header">Dashboard Analytique</div>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Toutes les visualisations sont calculées en temps réel depuis la base de données des prédictions.</p>', unsafe_allow_html=True)

# ── Filtres ────────────────────────────────────────────────────
if has:
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        opts_c = ["Toutes"] + sorted(df["culture"].dropna().unique().tolist())
        f_cult = st.selectbox("Culture", opts_c)
    with fc2:
        opts_z = ["Toutes"] + sorted(df["zone"].dropna().unique().tolist())
        f_zone = st.selectbox("Zone", opts_z)
    with fc3:
        opts_i = ["Toutes", "oui", "non"]
        f_irr  = st.selectbox("Irrigation", opts_i)

    dff = df.copy()
    if f_cult != "Toutes": dff = dff[dff["culture"] == f_cult]
    if f_zone != "Toutes": dff = dff[dff["zone"]    == f_zone]
    if f_irr  != "Toutes": dff = dff[dff["irrigation"] == f_irr]

    if dff.empty:
        st.warning("Aucune donnée ne correspond aux filtres.")
        st.stop()
else:
    dff = df

st.markdown("<br>", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────
if has:
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Prédictions",       str(len(dff)))
    k2.metric("Rendement moyen",   f"{dff['rendement_predit'].mean():.2f} t/ha")
    k3.metric("Meilleur rendement",f"{dff['rendement_predit'].max():.2f} t/ha")
    k4.metric("Zones actives",     str(dff["zone"].nunique()))
    st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("Aucune prédiction enregistrée pour le moment.")
    st.stop()

# ── Évolution temporelle ───────────────────────────────────────
st.markdown('<div class="section-header">Évolution des rendements</div>', unsafe_allow_html=True)
fig_time = go.Figure()
for i, cult in enumerate(dff["culture"].unique()):
    sub = dff[dff["culture"]==cult].sort_values("date_prediction")
    fig_time.add_trace(go.Scatter(
        x=sub["date_prediction"], y=sub["rendement_predit"], name=cult,
        mode="lines+markers",
        line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2),
        marker=dict(size=6),
        hovertemplate=f"<b>{cult}</b><br>%{{x|%d/%m %H:%M}}<br>%{{y:.2f}} t/ha<extra></extra>",
    ))
fig_time.update_layout(
    height=320, **CHART_LAYOUT,
    legend=dict(orientation="h", y=-0.25, font=dict(size=11)),
    xaxis=dict(showgrid=False, tickfont=dict(size=10), tickformat="%d/%m"),
    yaxis=dict(gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10), title="t/ha"),
)
st.plotly_chart(fig_time, use_container_width=True)

# ── Heatmap + Répartition ──────────────────────────────────────
col_heat, col_pie = st.columns([1.5, 1], gap="large")

with col_heat:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Heatmap rendement — culture × zone</div></div><div class="card-body">', unsafe_allow_html=True)
    pivot = dff.pivot_table(values="rendement_predit", index="culture", columns="zone", aggfunc="mean").round(2)
    if not pivot.empty:
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
            colorscale=[[0,"#EAF3DE"],[0.33,"#97C459"],[0.66,"#3D7A55"],[1,"#1A3528"]],
            text=[[f"{v:.2f}" if str(v)!="nan" else "—" for v in row] for row in pivot.values],
            texttemplate="%{text}", textfont={"size":11},
            hovertemplate="<b>%{y} / %{x}</b><br>%{z:.2f} t/ha<extra></extra>",
            showscale=True, colorbar=dict(title="t/ha", thickness=12, len=0.85),
        ))
        
        custom_layout = CHART_LAYOUT.copy()
        custom_layout.pop('margin', None) 
        
        fig_heat.update_layout(
            height=max(200, len(pivot)*40+60), **custom_layout,
            xaxis=dict(tickfont=dict(size=11), tickangle=-20),
            yaxis=dict(tickfont=dict(size=11)),
            margin=dict(t=10,b=10,l=10,r=50),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.plotly_chart(empty_fig(), use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_pie:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Répartition des cultures</div></div><div class="card-body">', unsafe_allow_html=True)
    cc = dff["culture"].value_counts().reset_index()
    cc.columns = ["Culture","N"]
    fig_pie = go.Figure(go.Pie(
        labels=cc["Culture"], values=cc["N"], hole=0.44,
        marker_colors=CHART_COLORS[:len(cc)],
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value} prédictions (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(
        height=260, **CHART_LAYOUT,
        legend=dict(font=dict(size=11), orientation="v"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Top cultures + Top zones ───────────────────────────────────
col_bar, col_zone = st.columns(2, gap="large")

with col_bar:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Rendement moyen par culture</div></div><div class="card-body">', unsafe_allow_html=True)
    rc = dff.groupby("culture")["rendement_predit"].mean().sort_values().reset_index()
    rc.columns = ["Culture","Rendement"]
    rc["Rendement"] = rc["Rendement"].round(2)
    fig_bar = go.Figure(go.Bar(
        y=rc["Culture"], x=rc["Rendement"], orientation="h",
        marker_color=CHART_COLORS[:len(rc)],
        text=[f"{v} t/ha" for v in rc["Rendement"]],
        textposition="outside", textfont=dict(size=11, family="DM Mono"),
        hovertemplate="<b>%{y}</b><br>%{x:.2f} t/ha<extra></extra>",
    ))
    fig_bar.update_layout(
        height=max(200, len(rc)*44+60), **CHART_LAYOUT,
        xaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=12)),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_zone:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Top zones par rendement moyen</div></div><div class="card-body">', unsafe_allow_html=True)
    rz = dff.groupby("zone")["rendement_predit"].mean().sort_values().reset_index()
    rz.columns = ["Zone","Rendement"]
    rz["Rendement"] = rz["Rendement"].round(2)
    fig_zone = go.Figure(go.Bar(
        y=rz["Zone"], x=rz["Rendement"], orientation="h",
        marker_color=["#1A3528", "#3D7A55", "#7FAF8A", "#B3D98F", "#EF9F27"][:len(rz)],
        text=[f"{v} t/ha" for v in rz["Rendement"]],
        textposition="outside", textfont=dict(size=11, family="DM Mono"),
    ))
    fig_zone.update_layout(
        height=max(200, len(rz)*44+60), **CHART_LAYOUT,
        xaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=12)),
    )
    st.plotly_chart(fig_zone, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Scatter + Box ──────────────────────────────────────────────
col_sc, col_box = st.columns(2, gap="large")

with col_sc:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Corrélation engrais vs rendement</div></div><div class="card-body">', unsafe_allow_html=True)
    fig_sc = go.Figure()
    for i, cult in enumerate(dff["culture"].unique()):
        sub = dff[dff["culture"]==cult]
        fig_sc.add_trace(go.Scatter(
            x=sub["engrais"], y=sub["rendement_predit"],
            mode="markers", name=cult,
            marker=dict(color=CHART_COLORS[i%len(CHART_COLORS)], size=9, opacity=0.85),
            hovertemplate=f"<b>{cult}</b><br>Engrais : %{{x}} kg/ha<br>Rendement : %{{y:.2f}} t/ha<extra></extra>",
        ))
    fig_sc.update_layout(
        height=260, **CHART_LAYOUT,
        legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
        xaxis=dict(title="Engrais (kg/ha)", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        yaxis=dict(title="Rendement (t/ha)", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_sc, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_box:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Distribution rendements par zone</div></div><div class="card-body">', unsafe_allow_html=True)
    fig_box = go.Figure()
    for i, z in enumerate(dff["zone"].unique()):
        sub = dff[dff["zone"]==z]
        fig_box.add_trace(go.Box(
            y=sub["rendement_predit"], name=z,
            marker_color=CHART_COLORS[i%len(CHART_COLORS)],
            boxpoints="all", jitter=0.3, pointpos=-1.6,
        ))
    fig_box.update_layout(
        height=260, **CHART_LAYOUT,
        yaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=11)),
        legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
    )
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Irrigation + Température ───────────────────────────────────
col_irr, col_temp = st.columns(2, gap="large")

with col_irr:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Irrigation — impact rendement</div></div><div class="card-body">', unsafe_allow_html=True)
    ig = dff.groupby("irrigation")["rendement_predit"].agg(["mean","count"]).reset_index()
    ig.columns = ["Irrigation","Rendement","N"]
    ig["Rendement"] = ig["Rendement"].round(2)
    fig_irr = go.Figure(go.Bar(
        x=ig["Irrigation"], y=ig["Rendement"],
        marker_color=["#3D7A55" if v=="oui" else "#C05A2E" for v in ig["Irrigation"]],
        text=[f"{v} t/ha  ({n})" for v,n in zip(ig["Rendement"],ig["N"])],
        textposition="outside", width=0.45,
    ))
    fig_irr.update_layout(
        height=240, **CHART_LAYOUT,
        xaxis=dict(tickfont=dict(size=12), showgrid=False),
        yaxis=dict(title="t/ha", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_irr, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_temp:
    st.markdown('<div class="card"><div class="card-head"><div class="card-title">Température vs rendement</div></div><div class="card-body">', unsafe_allow_html=True)
    fig_temp = go.Figure()
    for i, cult in enumerate(dff["culture"].unique()):
        sub = dff[dff["culture"]==cult]
        fig_temp.add_trace(go.Scatter(
            x=sub["temperature"], y=sub["rendement_predit"],
            mode="markers", name=cult,
            marker=dict(color=CHART_COLORS[i%len(CHART_COLORS)], size=8, opacity=0.82),
        ))
    fig_temp.update_layout(
        height=240, **CHART_LAYOUT,
        legend=dict(orientation="h", y=-0.35, font=dict(size=10)),
        xaxis=dict(title="Température (°C)", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
        yaxis=dict(title="Rendement (t/ha)", gridcolor="rgba(100,100,100,0.12)", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Insight auto ───────────────────────────────────────────────
best  = dff.sort_values("rendement_predit", ascending=False).iloc[0]
worst = dff.sort_values("rendement_predit").iloc[0]
st.markdown(f"""
<div class="interpret-box">
    <div class="interpret-box-label">Insight IA — données réelles</div>
    <p>
        Meilleur rendement : <strong>{best['culture']}</strong> à <strong>{best['zone']}</strong>
        → <strong>{best['rendement_predit']} t/ha</strong>.
        Rendement le plus faible : <strong>{worst['culture']}</strong> à <strong>{worst['zone']}</strong>
        → <strong>{worst['rendement_predit']} t/ha</strong>.
    </p>
</div>""", unsafe_allow_html=True)

# ── Carte ──────────────────────────────────────────────────────
if "latitude" in dff.columns:
    st.markdown('<div class="section-header">Carte des prédictions</div>', unsafe_allow_html=True)
    st.map(dff.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]].dropna())

footer()