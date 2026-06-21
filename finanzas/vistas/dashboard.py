"""Vista Dashboard: resumen del mes activo."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from finanzas import db, reportes
from finanzas.config import COLORES
from finanzas.formato import pesos


def render(mes):
    r = reportes.resumen_mes(mes)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💚 Ingresos reales", pesos(r["ingresos_real"]),
              help="Suma de tus ingresos del mes.")
    c2.metric("💸 Gastos mensuales", pesos(r["gastos_mens_real"]),
              help="Presupuesto mensual de gastos (Real). No incluye compras "
                   "libres.")
    c3.metric("🛒 Gasto diario", pesos(r["compras_real"]),
              help="Compras libres: tu gasto del día a día (almuerzos, "
                   "salidas, etc.).")
    c4.metric("🏦 Ahorros", pesos(r["ahorros_real"]),
              help="Suma de la columna Real de tus ahorros.")
    disp = r["disponible"]
    c5.metric("💰 Disponible para gastar", pesos(disp),
              delta="En verde si es positivo",
              delta_color="normal" if disp >= 0 else "inverse",
              help="Ingresos reales − presupuesto mensual de gastos COMPLETO "
                   "(reservado aunque no lo hayas pagado) − gasto diario − "
                   "ahorros − invertido − cuota de deudas del mes (reservada).")

    st.divider()
    g1, g2 = st.columns([3, 2])

    # --- Presupuesto vs Real por sección ---
    cats = ["Compras libres", "Gastos mensuales", "Ahorros", "Deudas"]
    secs = ["compra_libre", "gasto", "ahorro", "deuda"]
    dfs = {s: db.cargar_seccion(mes, s) for s in secs}

    def suma(df, col):
        return float(df[col].sum()) if col in df and not df.empty else 0.0

    presu = [suma(dfs[s], "presupuesto") for s in secs]
    reales = [suma(dfs[s], "real") for s in secs]

    with g1:
        st.subheader("Presupuesto vs Real")
        fig = go.Figure()
        fig.add_bar(name="Presupuesto", x=cats, y=presu,
                    marker_color=COLORES["gris"])
        fig.add_bar(name="Real", x=cats, y=reales,
                    marker_color=COLORES["primario"])
        fig.update_layout(barmode="group", height=360,
                          margin=dict(t=10, b=10, l=10, r=10),
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, width="stretch")

    with g2:
        st.subheader("Distribución de gastos")
        cat_gastos = reportes.gastos_por_categoria(mes)
        if cat_gastos:
            fig_p = px.pie(names=list(cat_gastos.keys()),
                           values=list(cat_gastos.values()), hole=0.45)
            fig_p.update_traces(textposition="inside", textinfo="percent+label")
            fig_p.update_layout(height=360, margin=dict(t=10, b=10, l=10, r=10),
                                showlegend=False)
            st.plotly_chart(fig_p, width="stretch")
        else:
            st.info("Sin gastos registrados este mes.")

    st.divider()
    st.subheader("Resumen por sección")
    resumen_df = pd.DataFrame({
        "Sección": cats,
        "Presupuesto": presu,
        "Real": reales,
        "Diferencia": [p - x for p, x in zip(presu, reales)],
    })
    st.dataframe(
        resumen_df.style.format(
            {"Presupuesto": pesos, "Real": pesos, "Diferencia": pesos}),
        width="stretch", hide_index=True)
