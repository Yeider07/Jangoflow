"""Vista Histórico: evolución mes a mes."""

import plotly.graph_objects as go
import streamlit as st

from finanzas import reportes
from finanzas.config import COLORES
from finanzas.formato import etiqueta_mes, pesos


def render():
    hist = reportes.resumen_historico()
    if hist.empty:
        st.info("Aún no hay meses para comparar.")
        return

    hist["Mes"] = hist["mes"].map(etiqueta_mes)

    with st.container(key="dashcard_hist_evolucion"):
        st.subheader("Evolución: Ingresos vs Gastos vs Ahorros (Real)")
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
        fig1.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10),
                           legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig1, width="stretch")

    with st.container(key="dashcard_hist_disponible"):
        st.subheader("Disponible para gastar por mes")
        colores = [COLORES["exito"] if v >= 0 else COLORES["peligro"]
                   for v in hist["disponible"]]
        fig2 = go.Figure(go.Bar(x=hist["Mes"], y=hist["disponible"],
                                marker_color=colores, marker_cornerradius=6))
        fig2.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, width="stretch")

    with st.container(key="dashcard_hist_tabla"):
        st.subheader("Tabla comparativa")
        tabla = hist[["Mes", "ingresos_real", "gastos_real", "ahorros_real",
                      "deudas_real", "disponible"]].copy()
        tabla.columns = ["Mes", "Ingresos", "Gastos", "Ahorros", "Deudas",
                         "Disponible"]
        st.dataframe(
            tabla.style.format({c: pesos for c in
                                ["Ingresos", "Gastos", "Ahorros", "Deudas",
                                 "Disponible"]}),
            width="stretch", hide_index=True)
