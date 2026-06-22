"""Barra lateral: selector de sección y gestión de meses."""

import datetime as dt

import streamlit as st

from finanzas import db
from finanzas.config import MESES_ES
from finanzas.formato import etiqueta_mes, mes_por_defecto

# Etiquetas de las secciones principales (también usadas por el enrutador)
VISTA_FINANZAS = "💰 Finanzas"
VISTA_TARJETA = "💳 Tarjeta de crédito"
VISTA_HIPOTECARIO = "🏠 Crédito hipotecario"

# Editores globales que NO deben limpiarse al cambiar de mes
_EDITORES_GLOBALES = (
    "ed_tarjeta_act", "ed_tarjeta_pag", "ed_prest_act", "ed_prest_pag",
)


def seleccionar_vista():
    """Radio con la sección principal. Devuelve la vista elegida."""
    vista = st.sidebar.radio(
        "📂 Sección",
        [VISTA_FINANZAS, VISTA_TARJETA, VISTA_HIPOTECARIO],
        key="vista_app",
    )
    st.sidebar.divider()
    return vista


def gestionar_meses():
    """Crea/selecciona/elimina meses en la barra lateral. Devuelve el mes activo
    (o detiene la app si todavía no hay meses)."""
    st.sidebar.title(VISTA_FINANZAS)
    meses = db.listar_meses()

    with st.sidebar.expander("➕ Crear nuevo mes", expanded=not meses):
        hoy = dt.date.today()
        col_a, col_m = st.columns(2)
        anio = col_a.number_input("Año", 2020, 2100, hoy.year, step=1)
        mes_num = col_m.selectbox(
            "Mes", list(MESES_ES.keys()), index=hoy.month - 1,
            format_func=lambda m: MESES_ES[m])
        nuevo_mes = f"{int(anio):04d}-{int(mes_num):02d}"

        copiar = None
        if meses and st.checkbox(
                "Copiar TODO de otro mes", value=True,
                help="Trae todo tal cual (presupuesto, real, fechas) para que "
                     "lo ajustes a tu gusto."):
            copiar = st.selectbox("Copiar de", meses,
                                  format_func=etiqueta_mes, key="copiar_de")

        if st.button("Crear mes", width="stretch"):
            if nuevo_mes in meses:
                st.warning(f"El mes {etiqueta_mes(nuevo_mes)} ya existe.")
            else:
                db.crear_mes(nuevo_mes, copiar_de=copiar)
                st.success(f"Mes {etiqueta_mes(nuevo_mes)} creado.")
                st.rerun()

    meses = db.listar_meses()
    if not meses:
        st.info("👈 Crea tu primer mes en la barra lateral para empezar.")
        st.stop()

    # Por defecto, situarse en el mes vencido (el calendario anterior a hoy);
    # si no existe, el mes pasado más reciente disponible. 'meses' va de más
    # nuevo a más viejo. Solo aplica al abrir la app: luego respeta la elección.
    objetivo = mes_por_defecto()
    pasados = [m for m in meses if m <= objetivo]
    idx_def = meses.index(pasados[0]) if pasados else 0
    mes = st.sidebar.selectbox(
        "📅 Mes activo", meses, index=idx_def,
        format_func=etiqueta_mes, key="mes_activo")

    # Al cambiar de mes, limpiar el estado de las tablas editables por mes.
    # Evita que Streamlit reaplique cambios viejos (deltas) al mes equivocado.
    if st.session_state.get("_ultimo_mes") != mes:
        for _k in list(st.session_state.keys()):
            if _k.startswith("editor_") and _k not in _EDITORES_GLOBALES:
                del st.session_state[_k]
        st.session_state["_ultimo_mes"] = mes

    with st.sidebar.expander("🗑️ Eliminar mes"):
        st.caption(f"Vas a borrar **{etiqueta_mes(mes)}** y todos sus "
                   "registros. Esta acción no se puede deshacer.")
        confirmar = st.checkbox("Sí, entiendo y quiero eliminarlo",
                                key="conf_del")
        if st.button("Eliminar mes definitivamente", width="stretch",
                     disabled=not confirmar):
            db.eliminar_mes(mes)
            st.success(f"Mes {etiqueta_mes(mes)} eliminado.")
            st.rerun()

    st.sidebar.caption(
        "Tus datos se guardan localmente en **finanzas.db** "
        "(en la carpeta del proyecto).")
    return mes
