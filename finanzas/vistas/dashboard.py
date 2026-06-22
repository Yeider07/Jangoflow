"""Vista Dashboard: resumen del mes activo (diseño minimalista)."""

import plotly.graph_objects as go
import streamlit as st

from finanzas import categorias, db, grafico, reportes
from finanzas.formato import pesos

# CSS minimalista: métricas más ligeras, etiquetas tenues, menos peso visual.
_CSS = """
<style>
[data-testid="stMetricValue"] { font-weight: 400; font-size: 1.85rem; }
[data-testid="stMetricLabel"] p {
    font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
    opacity: 0.55;
}
hr { margin: 0.4rem 0; opacity: 0.12; }
</style>
"""


def render(mes):
    st.markdown(_CSS, unsafe_allow_html=True)
    r = reportes.resumen_mes(mes)

    # --- Métricas clave (limpias, sin cajas) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", pesos(r["ingresos_real"]))
    c2.metric("Gastos del mes", pesos(r["gastos_real"]))
    c3.metric("Ahorro", pesos(r["ahorros_real"]))
    disp = r["disponible"]
    c4.metric("Disponible", pesos(disp),
              delta="positivo" if disp >= 0 else "en rojo",
              delta_color="normal" if disp >= 0 else "inverse")

    st.write("")

    # --- En qué se va el dinero (categorías) | Gasto día a día ---
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("##### En qué se va el dinero")
        _grafico_categorias(mes)
    with g2:
        st.markdown("##### Gasto día a día")
        _grafico_gasto_diario(mes)

    st.write("")

    # --- Presupuesto vs Real por sección ---
    st.markdown("##### Presupuesto vs real")
    _grafico_presupuesto(mes)


def _grafico_categorias(mes):
    """Barras horizontales del gasto por categoría automática."""
    cats = reportes.gastos_categorizados(mes)
    if not cats:
        st.caption("Sin gastos registrados este mes.")
        return
    # Mayor arriba: en barras horizontales el primero queda abajo, así que
    # invertimos el orden (cats viene de mayor a menor).
    nombres = list(cats.keys())[::-1]
    valores = [cats[n] for n in nombres]
    etiquetas = [categorias.etiqueta(n) for n in nombres]
    colores = [categorias.color(n) for n in nombres]

    fig = go.Figure(go.Bar(
        x=valores, y=etiquetas, orientation="h", marker_color=colores,
        text=[pesos(v) for v in valores], textposition="auto",
        hovertemplate="%{y}: %{text}<extra></extra>"))
    grafico.estilizar(fig, alto=300, grid_y=False, grid_x=True, leyenda=False)
    st.plotly_chart(fig, theme=None, width="stretch")

    total = sum(cats.values())
    top = max(cats, key=cats.get)
    st.caption(f"Total **{pesos(total)}** · lidera **{categorias.etiqueta(top)}** "
               f"({cats[top] / total * 100:.0f}%)")


def _grafico_gasto_diario(mes):
    """Barras del gasto diario (compras libres) a lo largo del mes."""
    gd = reportes.gasto_diario(mes)
    if gd.empty:
        st.caption("Sin compras libres con fecha este mes.")
        return
    fig = go.Figure(go.Bar(
        x=gd["fecha"], y=gd["total"], marker_color=grafico.PALETA[0],
        hovertemplate="%{x|%d %b}: $%{y:,.0f}<extra></extra>"))
    grafico.estilizar(fig, alto=300, grid_y=True, leyenda=False)
    fig.update_xaxes(tickformat="%d %b", dtick="D7")
    st.plotly_chart(fig, theme=None, width="stretch")

    total = float(gd["total"].sum())
    dias = len(gd)
    st.caption(f"Total **{pesos(total)}** en **{dias} día(s)** con gasto · "
               f"promedio **{pesos(total / dias)}**/día")


def _grafico_presupuesto(mes):
    """Barras agrupadas presupuesto vs real por sección."""
    cats = ["Compras libres", "Gastos mensuales", "Ahorros", "Deudas"]
    secs = ["compra_libre", "gasto", "ahorro", "deuda"]
    dfs = {s: db.cargar_seccion(mes, s) for s in secs}

    def suma(df, col):
        return float(df[col].sum()) if col in df and not df.empty else 0.0

    presu = [suma(dfs[s], "presupuesto") for s in secs]
    reales = [suma(dfs[s], "real") for s in secs]

    if not any(presu) and not any(reales):
        st.caption("Sin datos para comparar este mes.")
        return

    fig = go.Figure()
    fig.add_bar(name="Presupuesto", x=cats, y=presu,
                marker_color=grafico.COLOR_TENUE)
    fig.add_bar(name="Real", x=cats, y=reales, marker_color=grafico.PALETA[0])
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
    grafico.estilizar(fig, alto=300)
    st.plotly_chart(fig, theme=None, width="stretch")
