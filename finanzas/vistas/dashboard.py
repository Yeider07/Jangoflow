"""Vista Dashboard: resumen del mes activo (diseño minimalista)."""

import plotly.graph_objects as go
import streamlit as st

from finanzas import categorias, db, grafico, reportes
from finanzas.formato import pesos

# El sistema de diseño (tarjetas glass 'dashcard_*', KPIs, secciones) vive en el
# CSS global de app_finanzas.py para que aplique también a las vistas aisladas.


def _md(texto):
    """Escapa el '$' para que Streamlit no lo interprete como LaTeX."""
    return texto.replace("$", "\\$")


def _kpi(label, valor, pct="", delta=None, positivo=True):
    """Una tarjeta del grid de KPIs (HTML propio para que sea responsive)."""
    pct_html = f" · {pct}" if pct else ""
    delta_html = ""
    if delta:
        clase = "pos" if positivo else "neg"
        delta_html = f'<div class="kpi-delta {clase}">{delta}</div>'
    return (f'<div class="kpi"><div class="kpi-label">{label}{pct_html}</div>'
            f'<div class="kpi-value">{valor}</div>{delta_html}</div>')


def render(mes):
    r = reportes.resumen_mes(mes)

    # --- Métricas clave: grid responsive (6 en escritorio, 2 por fila en móvil) ---
    # El % junto a cada etiqueta es la porción sobre los ingresos del mes.
    ing = r["ingresos_real"]

    def _p(parte):
        return f"{parte / ing * 100:.0f}%" if ing else ""

    disp = r["disponible"]
    kpis = "".join([
        _kpi("Ingresos", pesos(ing)),
        _kpi("Gastos del mes", pesos(r["gastos_real"]), _p(r["gastos_real"])),
        _kpi("Gastos fijos", pesos(r["gastos_mens_real"]),
             _p(r["gastos_mens_real"])),
        _kpi("Gastos diarios", pesos(r["compras_real"]), _p(r["compras_real"])),
        _kpi("Ahorro", pesos(r["ahorros_real"]), _p(r["ahorros_real"])),
        _kpi("Disponible", pesos(disp), _p(disp),
             delta="↑ positivo" if disp >= 0 else "↓ en rojo",
             positivo=disp >= 0),
    ])
    st.markdown(f'<div class="kpis">{kpis}</div>', unsafe_allow_html=True)

    st.write("")

    # --- Gastos diarios (compras libres): dos tarjetas ---
    st.markdown('<div class="dash-section">Gastos diarios · compras libres</div>',
                unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1, st.container(key="dashcard_categorias"):
        st.markdown("##### En qué se va el dinero")
        _grafico_categorias(mes)
    with g2, st.container(key="dashcard_diario"):
        st.markdown("##### Gasto día a día")
        _grafico_gasto_diario(mes)

    # Drill-down de sub-categorías, oculto en un desplegable.
    _detalle_categoria(mes)

    st.write("")

    # --- Gastos fijos mensuales (tarjeta, por su nombre real) ---
    with st.container(key="dashcard_fijos"):
        st.markdown("##### Gastos fijos mensuales")
        _grafico_gastos_fijos(mes)

    st.write("")

    # --- Presupuesto vs real por sección (tarjeta, visión general) ---
    with st.container(key="dashcard_presupuesto"):
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
        marker_cornerradius=7,
        text=[pesos(v) for v in valores], textposition="auto",
        hovertemplate="%{y}: %{text}<extra></extra>"))
    grafico.estilizar(fig, alto=300, grid_y=False, grid_x=True, leyenda=False)
    st.plotly_chart(fig, theme=None, width="stretch", config=grafico.SIN_BARRA)

    total = sum(cats.values())
    top = max(cats, key=cats.get)
    st.caption(_md(f"Total **{pesos(total)}** · lidera "
                   f"**{categorias.etiqueta(top)}** "
                   f"({cats[top] / total * 100:.0f}%)"))


def _grafico_gasto_diario(mes):
    """Barras del gasto diario (compras libres) a lo largo del mes."""
    gd = reportes.gasto_diario(mes)
    if gd.empty:
        st.caption("Sin compras libres con fecha este mes.")
        return
    fig = go.Figure(go.Bar(
        x=gd["fecha"], y=gd["total"], marker_color=grafico.PALETA[0],
        marker_cornerradius=9,
        hovertemplate="%{x|%d %b}: $%{y:,.0f}<extra></extra>"))
    grafico.estilizar(fig, alto=300, grid_y=True, leyenda=False)
    fig.update_xaxes(tickformat="%d %b", tickangle=-40)
    st.plotly_chart(fig, theme=None, width="stretch", config=grafico.SIN_BARRA)

    total = float(gd["total"].sum())
    dias = len(gd)
    st.caption(_md(f"Total **{pesos(total)}** en **{dias} día(s)** con gasto · "
                   f"promedio **{pesos(total / dias)}**/día"))


def _detalle_categoria(mes):
    """Selector de categoría -> sus descripciones reales (sub-categorías).

    Va dentro de un desplegable cerrado por defecto: las sub-categorías quedan
    ocultas y solo se muestran si el usuario abre el detalle y elige una."""
    cats = reportes.gastos_categorizados(mes)
    if not cats:
        return
    with st.expander("🔎 Detalle de una categoría", expanded=False):
        sel = st.selectbox(
            "Categoría", list(cats.keys()), key=f"detalle_cat_{mes}",
            label_visibility="collapsed",
            format_func=lambda c: f"{categorias.etiqueta(c)}  ·  {pesos(cats[c])}")

        detalle = reportes.gasto_detalle_categoria(mes, sel)
        if not detalle:
            st.caption("Sin movimientos en esta categoría.")
            return

        nombres = list(detalle.keys())[::-1]
        valores = [detalle[n] for n in nombres]
        fig = go.Figure(go.Bar(
            x=valores, y=nombres, orientation="h",
            marker_color=categorias.color(sel), marker_cornerradius=7,
            text=[pesos(v) for v in valores], textposition="auto",
            hovertemplate="%{y}: %{text}<extra></extra>"))
        grafico.estilizar(fig, alto=max(140, 42 * len(nombres)),
                          grid_y=False, grid_x=True, leyenda=False)
        st.plotly_chart(fig, theme=None, width="stretch",
                        config=grafico.SIN_BARRA)
        st.caption(_md(f"**{len(detalle)}** concepto(s) en "
                       f"**{categorias.etiqueta(sel)}** · suman "
                       f"**{pesos(sum(detalle.values()))}**"))


def _grafico_gastos_fijos(mes):
    """Barras presupuesto vs real de cada gasto fijo mensual (por su nombre).

    A diferencia de las compras libres, los gastos fijos no se categorizan: se
    muestran tal cual los nombró el usuario (Plan de datos, Parqueadero...)."""
    df = db.cargar_seccion(mes, "gasto")
    df = df[(df["nombre"] != "") &
            ((df["presupuesto"] != 0) | (df["real"] != 0))]
    if df.empty:
        st.caption("Sin gastos fijos registrados este mes.")
        return

    # Mayor arriba: en barras horizontales el primero queda abajo, así que
    # ordenamos ascendente por el mayor entre presupuesto y real.
    df = df.assign(_tope=df[["presupuesto", "real"]].max(axis=1))
    df = df.sort_values("_tope")
    nombres = df["nombre"].tolist()

    fig = go.Figure()
    fig.add_bar(name="Presupuesto", y=nombres, x=df["presupuesto"],
                orientation="h", marker_color=grafico.COLOR_TENUE,
                marker_cornerradius=5,
                hovertemplate="%{y} · presupuesto: $%{x:,.0f}<extra></extra>")
    fig.add_bar(name="Real", y=nombres, x=df["real"], orientation="h",
                marker_color=grafico.PALETA[0], marker_cornerradius=5,
                hovertemplate="%{y} · real: $%{x:,.0f}<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.1)
    grafico.estilizar(fig, alto=max(220, 56 * len(nombres)),
                      grid_y=False, grid_x=True)
    st.plotly_chart(fig, theme=None, width="stretch", config=grafico.SIN_BARRA)

    tp = float(df["presupuesto"].sum())
    tr = float(df["real"].sum())
    st.caption(_md(f"Real **{pesos(tr)}** de **{pesos(tp)}** presupuestado "
                   f"· **{len(nombres)}** gasto(s) fijo(s)"))


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
                marker_color=grafico.COLOR_TENUE, marker_cornerradius=5)
    fig.add_bar(name="Real", x=cats, y=reales, marker_color=grafico.PALETA[0],
                marker_cornerradius=5)
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
    grafico.estilizar(fig, alto=300)
    st.plotly_chart(fig, theme=None, width="stretch", config=grafico.SIN_BARRA)
