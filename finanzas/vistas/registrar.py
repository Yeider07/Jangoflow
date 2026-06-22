"""Vista Registrar / Editar: tablas editables por mes (sub-pestañas)."""

import datetime as dt

import pandas as pd
import streamlit as st

from finanzas import db
from finanzas.formato import pesos

# (clave de sección, etiqueta de la pestaña, singular para el botón guardar)
SECCIONES_UI = [
    ("ingreso", "💚 Ingresos", "ingreso"),
    ("compra_libre", "🛒 Compras libres", "compra libre"),
    ("gasto", "💸 Gastos", "gasto"),
    ("ahorro", "🏦 Ahorros", "ahorro"),
    ("invertido", "📈 Invertido", "invertido"),
    ("deuda", "🧾 Deudas", "deuda"),
]

# Etiqueta específica de la columna "real" según la sección
ETIQUETAS_REAL = {
    "compra_libre": "Gasto", "ingreso": "Monto", "ahorro": "Ahorrado",
    "invertido": "Invertido", "deuda": "Pagado",
}

CAPTIONS = {
    "ahorro": "**Ahorrado**: lo que ahorraste ESTE mes (líquido). En General se "
              "suma para ver tu ahorro total.",
    "invertido": "**Invertido**: lo que invertiste ESTE mes (no líquido, pero "
                 "sigue siendo tuyo). En General se suma.",
    "deuda": "**Total deuda**: el monto completo que debes. **Cuota mes**: lo "
             "que pagas este mes (se reserva del disponible). **Pagado**: lo "
             "que realmente pagaste.",
}


def _column_config(seccion, columnas, hoy):
    """Configuración de columnas del editor para una sección."""
    base = {
        "nombre": st.column_config.TextColumn("Nombre", width="medium"),
        "fecha": st.column_config.DateColumn(
            "Fecha", format="DD-MM-YYYY", default=hoy),
        "total": st.column_config.NumberColumn(
            "Total deuda", format="localized", min_value=0),
        "presupuesto": st.column_config.NumberColumn(
            "Presupuesto", format="localized", min_value=0),
        "real": st.column_config.NumberColumn(
            "Real", format="localized", min_value=0),
    }
    cfg = {c: base[c] for c in columnas}
    if seccion in ETIQUETAS_REAL:
        cfg["real"] = st.column_config.NumberColumn(
            ETIQUETAS_REAL[seccion], format="localized", min_value=0)
    if seccion == "deuda":
        cfg["presupuesto"] = st.column_config.NumberColumn(
            "Cuota mes", format="localized", min_value=0)
    return cfg


def _pie(seccion, editado):
    """Totales al pie del editor."""
    if editado.empty or "real" not in editado:
        return
    tot_r = float(pd.to_numeric(editado["real"], errors="coerce").sum())
    if seccion == "deuda":
        tot_c = float(pd.to_numeric(editado["presupuesto"], errors="coerce").sum())
        c1, c2 = st.columns(2)
        c1.caption(f"Cuota del mes: **{pesos(tot_c)}**")
        c2.caption(f"Pagado: **{pesos(tot_r)}**")
    elif seccion == "ingreso":
        st.caption(f"Total ingresos: **{pesos(tot_r)}**")
    elif seccion == "ahorro":
        st.caption(f"Ahorrado este mes: **{pesos(tot_r)}**")
    elif seccion == "invertido":
        st.caption(f"Invertido este mes: **{pesos(tot_r)}**")
    elif "presupuesto" in editado:
        tot_p = float(pd.to_numeric(editado["presupuesto"], errors="coerce").sum())
        c1, c2, c3 = st.columns(3)
        c1.caption(f"Presupuesto: **{pesos(tot_p)}**")
        c2.caption(f"Real: **{pesos(tot_r)}**")
        c3.caption(f"Diferencia: **{pesos(tot_p - tot_r)}**")
    else:
        st.caption(f"Total gastado: **{pesos(tot_r)}**")


def render(mes):
    st.caption(
        "Edita como en Excel: escribe, agrega filas con ➕, borra seleccionando "
        "la fila. Pulsa **💾 Guardar** en cada sección para conservar los cambios.")
    hoy = dt.date.today()
    sub_tabs = st.tabs([t for _, t, _ in SECCIONES_UI])

    for (seccion, titulo, singular), sub in zip(SECCIONES_UI, sub_tabs):
        with sub, st.container(key=f"dashcard_reg_{seccion}"):
            if seccion in CAPTIONS:
                st.caption(CAPTIONS[seccion])
            df = db.cargar_seccion(mes, seccion)
            editado = st.data_editor(
                df, key=f"editor_{seccion}_{mes}", num_rows="dynamic",
                width="stretch", hide_index=True,
                column_config=_column_config(seccion, df.columns, hoy))
            _pie(seccion, editado)
            if st.button(f"💾 Guardar {singular}", key=f"save_{seccion}_{mes}"):
                db.guardar_seccion(mes, seccion, editado)
                st.session_state.pop(f"editor_{seccion}_{mes}", None)
                st.success(f"{titulo} guardado.")
                st.rerun()
