"""Vista General: patrimonio acumulado y gráficas (filtrable por meses)."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finanzas import db, reportes
from finanzas.config import COLORES, PALETA_AHORROS
from finanzas.formato import etiqueta_mes, pesos


def _grafica_total_vs_pagado(items, etiqueta_pagado, color_pagado):
    """Barras apiladas (pagado/devuelto + pendiente) para deudas o préstamos."""
    nombres = [x[0] for x in items]
    totales = [x[1] for x in items]
    pagados = [x[2] for x in items]
    pendientes = [max(t - p, 0) for t, p in zip(totales, pagados)]
    fig = go.Figure()
    fig.add_bar(name=etiqueta_pagado, x=nombres, y=pagados,
                marker_color=color_pagado,
                text=[pesos(v) for v in pagados], textposition="auto")
    fig.add_bar(name="Pendiente", x=nombres, y=pendientes,
                marker_color=COLORES["peligro"],
                text=[pesos(v) for v in pendientes], textposition="auto")
    fig.update_layout(barmode="stack", height=320,
                      margin=dict(t=10, b=10, l=10, r=10),
                      legend=dict(orientation="h", y=1.14))
    return fig, nombres, totales, pagados, pendientes


def render():
    todos_meses = db.listar_meses()
    sel = st.multiselect(
        "📅 Meses a incluir en el resumen", options=todos_meses,
        default=todos_meses, format_func=etiqueta_mes,
        help="Elige qué meses sumar. Útil para proyectar cuánto puedes ahorrar.")
    meses_filtro = sel if sel else todos_meses
    if not sel:
        st.caption("No seleccionaste meses: mostrando **todos**.")

    tg = reportes.totales_generales(meses_filtro)
    st.caption(f"Resumen de **{tg['meses']} mes(es)** seleccionados "
               f"({', '.join(etiqueta_mes(m) for m in sorted(meses_filtro))}).")

    # --- Patrimonio ---
    st.subheader("💎 Patrimonio")
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("🏦 Ahorro total", pesos(tg["ahorros"]),
              help="Todo lo que has ahorrado (incluye el dinero que prestaste).")
    p2.metric("🤝 Prestado", pesos(tg["prestado_pendiente"]),
              delta="se descuenta", delta_color="off",
              help="Lo que prestaste y aún no te devuelven. Sale de tu ahorro.")
    p3.metric("💧 Ahorro líquido", pesos(tg["ahorro_liquido"]),
              help="Ahorro total − Prestado pendiente. Tu dinero disponible YA.")
    p4.metric("📈 Invertido", pesos(tg["invertido"]),
              help="Suma de lo que has invertido. Es tuyo, pero no líquido.")
    p5.metric("💎 Patrimonio total", pesos(tg["patrimonio"]),
              help="Ahorro total + Invertido (el prestado ya está dentro del "
                   "ahorro).")

    st.divider()
    st.subheader("📊 Flujo acumulado")
    g1, g2, g3 = st.columns(3)
    g1.metric("💚 Ingresos acumulados", pesos(tg["ingresos"]))
    g2.metric("💸 Gastos acumulados", pesos(tg["gastos"]))
    g3.metric("🧾 Deudas pagadas", pesos(tg["deudas"]))

    # --- Ahorros ---
    st.divider()
    st.subheader("🏦 Ahorros (líquido)")
    aho = reportes.ahorros_acumulados(meses_filtro)
    if aho.empty or aho["ahorro_mes"].sum() == 0:
        st.info("Aún no has registrado ahorros. Regístralos en "
                "**✏️ Registrar / Editar → 🏦 Ahorros**.")
    else:
        aho["Mes"] = aho["mes"].map(etiqueta_mes)
        c_izq, c_der = st.columns(2)
        with c_izq:
            st.caption("Ahorro acumulado mes a mes")
            fig_ac = go.Figure()
            fig_ac.add_trace(go.Scatter(
                x=aho["Mes"], y=aho["acumulado"], mode="lines+markers",
                name="Acumulado", fill="tozeroy",
                line=dict(color=COLORES["primario"], width=3)))
            fig_ac.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_ac, width="stretch")
        with c_der:
            st.caption("Ahorro de cada mes (por tipo)")
            detalle = reportes.ahorros_detalle_por_mes(meses_filtro)
            if not detalle.empty:
                fig_mes = go.Figure()
                etiquetas = [etiqueta_mes(m) for m in detalle.index]
                for i, nombre in enumerate(detalle.columns):
                    fig_mes.add_bar(
                        name=nombre, x=etiquetas, y=detalle[nombre],
                        marker_color=PALETA_AHORROS[i % len(PALETA_AHORROS)])
                fig_mes.update_layout(
                    barmode="stack", height=320,
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", y=1.14))
                st.plotly_chart(fig_mes, width="stretch")
            else:
                st.info("Sin ahorros por tipo.")

    # --- Invertido ---
    st.divider()
    st.subheader("📈 Invertido")
    inv = reportes.invertido_acumulado(meses_filtro)
    if inv.empty or inv["invertido_mes"].sum() == 0:
        st.info("Aún no has registrado inversiones. Regístralas en "
                "**✏️ Registrar / Editar → 📈 Invertido**.")
    else:
        inv["Mes"] = inv["mes"].map(etiqueta_mes)
        fig_inv = go.Figure()
        fig_inv.add_trace(go.Scatter(
            x=inv["Mes"], y=inv["acumulado"], mode="lines+markers",
            name="Invertido acumulado", fill="tozeroy",
            line=dict(color=COLORES["invertido"], width=3)))
        fig_inv.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_inv, width="stretch")

    # --- Prestado (global) ---
    st.divider()
    st.subheader("🤝 Prestado (por cobrar)")
    prestamos = reportes.prestamos_por_nombre()
    if prestamos:
        fig, nombres, totales, devueltos, pend = _grafica_total_vs_pagado(
            prestamos, "Devuelto", COLORES["exito"])
        st.plotly_chart(fig, width="stretch")
        tabla = pd.DataFrame({
            "Préstamo": nombres, "Total prestado": totales,
            "Devuelto": devueltos, "Por cobrar": pend})
        st.dataframe(tabla.style.format({
            "Total prestado": pesos, "Devuelto": pesos, "Por cobrar": pesos}),
            width="stretch", hide_index=True)
    else:
        st.info("Sin préstamos registrados. Agrégalos en la pestaña 🤝 Prestado.")

    # --- Deudas ---
    st.divider()
    st.subheader("🧾 Deudas: total vs pagado")
    deudas = reportes.deudas_por_nombre(meses_filtro)
    if deudas:
        fig, nombres, totales, pagados, pend = _grafica_total_vs_pagado(
            deudas, "Pagado", COLORES["exito"])
        st.plotly_chart(fig, width="stretch")
        tabla = pd.DataFrame({
            "Deuda": nombres, "Total": totales,
            "Pagado": pagados, "Pendiente": pend})
        st.dataframe(tabla.style.format({
            "Total": pesos, "Pagado": pesos, "Pendiente": pesos}),
            width="stretch", hide_index=True)
    else:
        st.info("Sin deudas registradas. Agrégalas en "
                "**✏️ Registrar / Editar → 🧾 Deudas**.")
