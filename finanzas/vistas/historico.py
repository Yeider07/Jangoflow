"""Vista Histórico: evolución mes a mes, gasto libre y tasa de ahorro."""

import plotly.graph_objects as go
import streamlit as st

from finanzas import categorias, grafico, reportes
from finanzas.config import COLORES
from finanzas.formato import etiqueta_mes, pesos


def _pct(parte, total):
    return parte / total * 100 if total else 0.0


def _md(texto):
    return texto.replace("$", "\\$")


def render():
    hist = reportes.resumen_historico()
    if hist.empty:
        st.info("Aún no hay meses para comparar.")
        return

    hist = hist.sort_values("mes").reset_index(drop=True)
    hist["Mes"] = hist["mes"].map(etiqueta_mes)
    hist["tasa_ahorro"] = [
        _pct(a, i) for a, i in zip(hist["ahorros_real"], hist["ingresos_real"])]

    n = len(hist)
    libre_prom = float(hist["compras_real"].mean())
    libre_total = float(hist["compras_real"].sum())
    ahorro_prom = float(hist["ahorros_real"].mean())
    con_ing = hist[hist["ingresos_real"] > 0]
    tasa_prom = float(con_ing["tasa_ahorro"].mean()) if not con_ing.empty else 0.0

    # --- Resumen del periodo (KPIs) ---
    with st.container(key="dashcard_hist_kpis"):
        st.subheader("📌 Resumen del periodo")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tasa de ahorro media", f"{tasa_prom:.0f}%",
                  help="Promedio mensual de ahorro ÷ ingresos.")
        k2.metric("Gasto libre / mes", pesos(libre_prom),
                  help="Promedio mensual de compras libres (gasto diario).")
        k3.metric("Ahorro / mes", pesos(ahorro_prom))
        k4.metric("Meses", str(n))

    # --- Evolución: ingresos vs gastos vs ahorros ---
    with st.container(key="dashcard_hist_evolucion"):
        st.subheader("📈 Evolución: ingresos vs gastos vs ahorros")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=hist["Mes"], y=hist["ingresos_real"],
                                  mode="lines+markers", name="Ingresos",
                                  line=dict(color=COLORES["exito"], width=3)))
        fig1.add_trace(go.Scatter(x=hist["Mes"], y=hist["gastos_real"],
                                  mode="lines+markers", name="Gastos",
                                  line=dict(color=COLORES["peligro"], width=3)))
        fig1.add_trace(go.Scatter(x=hist["Mes"], y=hist["ahorros_real"],
                                  mode="lines+markers", name="Ahorros",
                                  line=dict(color=COLORES["primario"], width=3)))
        grafico.estilizar(fig1, alto=360)
        st.plotly_chart(fig1, theme=None, width="stretch",
                        config=grafico.SIN_BARRA)

    # --- Gasto libre por mes ---
    with st.container(key="dashcard_hist_libre_mes"):
        st.subheader("🛒 Gasto libre por mes")
        fig = go.Figure(go.Bar(
            x=hist["Mes"], y=hist["compras_real"],
            marker_color=grafico.PALETA[0], marker_cornerradius=6,
            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>"))
        if libre_prom > 0:
            fig.add_hline(y=libre_prom, line_dash="dot",
                          line_color=grafico.COLOR_TENUE,
                          annotation_text=f"promedio {pesos(libre_prom)}",
                          annotation_position="top left",
                          annotation_font_color=grafico.COLOR_TENUE)
        grafico.estilizar(fig, alto=320, leyenda=False)
        st.plotly_chart(fig, theme=None, width="stretch",
                        config=grafico.SIN_BARRA)
        st.caption(_md(f"Total libre del periodo: **{pesos(libre_total)}** · "
                       f"promedio **{pesos(libre_prom)}**/mes"))

    # --- Gasto libre por categoría (qué usas más) ---
    with st.container(key="dashcard_hist_libre_cat"):
        st.subheader("🏷️ Gasto libre por categoría (qué usas más)")
        cats = reportes.gastos_libres_categorizados()
        if not cats:
            st.caption("Sin compras libres registradas.")
        else:
            nombres = list(cats.keys())            # ya viene de mayor a menor
            valores = [cats[c] for c in nombres]
            etiquetas = [categorias.etiqueta(c) for c in nombres]
            colores = [categorias.color(c) for c in nombres]
            tot = sum(valores)
            top = nombres[0]
            fig = go.Figure(go.Pie(
                labels=etiquetas, values=valores, hole=0.58, sort=False,
                direction="clockwise",
                marker=dict(colors=colores,
                            line=dict(color="#0E1117", width=2)),
                textposition="inside", textinfo="percent",
                hovertemplate="%{label}: $%{value:,.0f} "
                              "(%{percent})<extra></extra>"))
            fig.update_layout(
                height=380, margin=dict(t=20, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family=grafico.FUENTE, color=grafico.COLOR_TEXTO,
                          size=13),
                hoverlabel=dict(bgcolor="#1A1F2B",
                                bordercolor="rgba(0,0,0,0)",
                                font=dict(family=grafico.FUENTE,
                                          color=grafico.COLOR_TEXTO)),
                legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center",
                            font=dict(size=12)),
                annotations=[dict(text=f"Total<br><b>{pesos(tot)}</b>",
                                  showarrow=False, x=0.5, y=0.5,
                                  font=dict(size=14,
                                            color=grafico.COLOR_TEXTO))])
            st.plotly_chart(fig, theme=None, width="stretch",
                            config=grafico.SIN_BARRA)
            st.caption(_md(f"Lidera **{categorias.etiqueta(top)}** "
                           f"({_pct(cats[top], tot):.0f}% del gasto libre) · "
                           f"promedio **{pesos(libre_prom)}**/mes"))

    # --- Disponible por mes ---
    with st.container(key="dashcard_hist_disponible"):
        st.subheader("💰 Disponible por mes")
        colores = [COLORES["exito"] if v >= 0 else COLORES["peligro"]
                   for v in hist["disponible"]]
        fig2 = go.Figure(go.Bar(x=hist["Mes"], y=hist["disponible"],
                                marker_color=colores, marker_cornerradius=6,
                                hovertemplate="%{x}: $%{y:,.0f}<extra></extra>"))
        grafico.estilizar(fig2, alto=300, leyenda=False)
        st.plotly_chart(fig2, theme=None, width="stretch",
                        config=grafico.SIN_BARRA)

    # --- Tabla comparativa ---
    with st.container(key="dashcard_hist_tabla"):
        st.subheader("📋 Tabla comparativa")
        tabla = hist[["Mes", "ingresos_real", "gastos_real", "compras_real",
                      "ahorros_real", "tasa_ahorro", "disponible"]].copy()
        tabla.columns = ["Mes", "Ingresos", "Gastos", "Gasto libre", "Ahorros",
                         "% Ahorro", "Disponible"]
        st.dataframe(
            tabla.style.format({
                "Ingresos": pesos, "Gastos": pesos, "Gasto libre": pesos,
                "Ahorros": pesos, "Disponible": pesos, "% Ahorro": "{:.0f}%"}),
            width="stretch", hide_index=True)
