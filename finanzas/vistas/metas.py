"""Vista Metas: pronóstico de ahorro y metas con progreso."""

import datetime as dt
import math

import plotly.graph_objects as go
import streamlit as st

from finanzas import db, reportes
from finanzas.config import COLORES
from finanzas.formato import (
    etiqueta_mes, fecha_larga, meses_a_texto, pesos, sumar_meses,
)


def render():
    st.subheader("🎯 Metas de ahorro y pronóstico")

    meses = sorted(db.listar_meses())   # ascendente
    st.markdown("#### 📈 Tu ritmo de ahorro")
    if not meses:
        st.info("Aún no has registrado ahorros. Regístralos en "
                "**✏️ Registrar / Editar → 🏦 Ahorros** para ver tu pronóstico.")
        return

    # El usuario elige desde qué mes se calcula el promedio y la proyección
    desde = st.selectbox(
        "Calcular el promedio desde el mes", meses, index=0,
        format_func=etiqueta_mes,
        help="El promedio mensual y la proyección se basan en este mes en "
             "adelante (útil para excluir meses iniciales atípicos).")
    filtrados = [m for m in meses if m >= desde]

    pron = reportes.pronostico_ahorro(filtrados)   # promedio del periodo elegido
    total_full = reportes.pronostico_ahorro()["total"]  # total real acumulado
    promedio = pron["promedio"]

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Ahorro promedio / mes", pesos(promedio),
              help=f"Promedio de {pron['meses']} mes(es), desde "
                   f"{etiqueta_mes(desde)}.")
    c2.metric("🏦 Total ahorrado", pesos(total_full),
              help="Todo lo ahorrado en todos los meses (no depende del filtro).")
    c3.metric("📆 Meses considerados", str(pron["meses"]))

    _proyeccion(promedio, total_full)

    # --- Metas ---
    st.divider()
    st.markdown("#### 🎯 Mis metas")
    st.caption("Define tus objetivos de ahorro y cuánto llevas. Te estimo "
               "cuándo los alcanzas según tu ritmo de ahorro.")

    df = db.cargar_metas()
    editado = st.data_editor(
        df, key="ed_metas", num_rows="dynamic", width="stretch",
        hide_index=True,
        column_config={
            "nombre": st.column_config.TextColumn("Meta", width="medium"),
            "objetivo": st.column_config.NumberColumn(
                "Objetivo", format="localized", min_value=0),
            "ahorrado": st.column_config.NumberColumn(
                "Ahorrado", format="localized", min_value=0),
        })

    if st.button("💾 Guardar metas"):
        db.guardar_metas(editado)
        st.session_state.pop("ed_metas", None)
        st.success("Metas guardadas.")
        st.rerun()

    _mostrar_metas(editado, promedio)


def _proyeccion(promedio, total_actual):
    """Gráfica de ahorro acumulado proyectado a futuro al ritmo promedio."""
    if promedio <= 0:
        st.caption("El promedio es 0 en el periodo elegido: no hay proyección.")
        return
    n = st.slider("Proyectar a cuántos meses", 3, 36, 12, step=3)
    hoy = dt.date.today()
    etiquetas = ["hoy"]
    valores = [total_actual]
    for k in range(1, n + 1):
        a, m = sumar_meses(hoy.year, hoy.month, k)
        etiquetas.append(fecha_larga(a, m).replace(" de ", "-"))
        valores.append(total_actual + promedio * k)

    fig = go.Figure(go.Scatter(
        x=etiquetas, y=valores, mode="lines+markers", fill="tozeroy",
        line=dict(color=COLORES["primario"], width=3)))
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10),
                      yaxis_title="Ahorro acumulado")
    st.plotly_chart(fig, width="stretch")

    a_fin, m_fin = sumar_meses(hoy.year, hoy.month, n)
    st.success(f"A este ritmo (**{pesos(promedio)}/mes**), en **{n} meses** "
               f"(**{fecha_larga(a_fin, m_fin)}**) tendrías "
               f"**{pesos(valores[-1])}** ahorrados.")


def _mostrar_metas(editado, promedio):
    """Barra de progreso y estimación de fecha para cada meta."""
    metas = editado.copy()
    metas["nombre"] = metas["nombre"].astype(str).str.strip()
    metas = metas[metas["nombre"] != ""]
    if metas.empty:
        st.caption("Aún no has definido metas. Agrega una arriba y guarda.")
        return

    hoy = dt.date.today()
    for _, fila in metas.iterrows():
        objetivo = float(fila.get("objetivo", 0) or 0)
        ahorrado = float(fila.get("ahorrado", 0) or 0)
        if objetivo <= 0:
            continue
        faltante = max(objetivo - ahorrado, 0)
        progreso = min(ahorrado / objetivo, 1.0)

        st.markdown(f"**{fila['nombre']}** — {pesos(ahorrado)} de "
                    f"{pesos(objetivo)}  ·  {progreso * 100:.0f}%")
        st.progress(progreso)

        if faltante <= 0:
            st.caption("✅ ¡Meta alcanzada! 🎉")
        elif promedio > 0:
            n = math.ceil(faltante / promedio)
            a, m = sumar_meses(hoy.year, hoy.month, n)
            st.caption(f"Faltan **{pesos(faltante)}**. A tu ritmo, la alcanzas "
                       f"en ~**{meses_a_texto(n)}** (**{fecha_larga(a, m)}**).")
        else:
            st.caption(f"Faltan **{pesos(faltante)}**. Registra ahorros para "
                       "estimar la fecha.")
        st.write("")
