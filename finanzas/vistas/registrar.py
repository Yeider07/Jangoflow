"""Vista Registrar / Editar: alta rápida por formulario + tabla para editar."""

import datetime as dt
import re

import pandas as pd
import streamlit as st

from finanzas import db
from finanzas.config import SECCIONES
from finanzas.formato import pesos

# (clave de sección, etiqueta de la pestaña, singular para los botones)
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


def _etiqueta(seccion, col):
    """Etiqueta legible de una columna para el formulario."""
    if col == "real":
        return ETIQUETAS_REAL.get(seccion, "Real")
    if col == "presupuesto":
        return "Cuota mes" if seccion == "deuda" else "Presupuesto"
    if col == "total":
        return "Total deuda"
    return col.capitalize()


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


def _form_agregar(mes, seccion, singular, hoy):
    """Formulario simple para agregar UN registro (cómodo en el celular).

    Usa campos nativos (texto, fecha, número) en vez de la tabla tipo Excel,
    que en móvil se corta y es difícil de tocar."""
    cols = SECCIONES[seccion]
    with st.form(key=f"add_{seccion}_{mes}", clear_on_submit=True):
        nombre = st.text_input("Nombre", placeholder="p. ej. Salchipapa")
        fecha = st.date_input("Fecha", value=hoy) if "fecha" in cols else None
        # Montos como text_input (no number_input): en móvil, dentro de un form,
        # el number_input a veces no confirma el valor al enviar y guardaba 0.
        # Aquí se teclea el número y se extraen los dígitos (acepta $ y puntos).
        montos = {}
        for col in ("total", "presupuesto", "real"):
            if col in cols:
                raw = st.text_input(_etiqueta(seccion, col) + " ($)",
                                    value="", placeholder="0")
                digitos = re.sub(r"[^\d]", "", raw or "")
                montos[col] = float(digitos) if digitos else 0.0
        enviado = st.form_submit_button(f"➕ Agregar {singular}",
                                        width="stretch", type="primary")

    if not enviado:
        return
    if not nombre.strip() and not any(montos.values()):
        st.warning("Escribe al menos un nombre o un monto.")
        return

    nueva = {"nombre": nombre.strip()}
    if "fecha" in cols:
        nueva["fecha"] = pd.to_datetime(fecha)
    nueva.update(montos)

    df = db.cargar_seccion(mes, seccion)
    df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
    db.guardar_seccion(mes, seccion, df)
    st.session_state.pop(f"editor_{seccion}_{mes}", None)
    st.success(f"{singular.capitalize()} agregado.")
    st.rerun()


def _pie(seccion, editado):
    """Totales al pie de la sección."""
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


def render_seccion(mes, seccion, singular):
    """Una sección editable del mes: formulario de alta + totales + tabla.

    Se renderiza dentro de la pestaña 'Este mes' (junto al resumen), que es
    donde se gestiona todo lo del mes activo."""
    hoy = dt.date.today()
    with st.container(key=f"dashcard_reg_{seccion}"):
        st.caption(
            "Agrega con el formulario **➕**. Para corregir o borrar, abre "
            "**✏️ Editar o borrar (tabla)** abajo.")
        if seccion in CAPTIONS:
            st.caption(CAPTIONS[seccion])

        _form_agregar(mes, seccion, singular, hoy)

        df = db.cargar_seccion(mes, seccion)
        _pie(seccion, df)

        with st.expander("✏️ Editar o borrar (tabla)", expanded=False):
            editado = st.data_editor(
                df, key=f"editor_{seccion}_{mes}", num_rows="dynamic",
                width="stretch", hide_index=True,
                column_config=_column_config(seccion, df.columns, hoy))
            if st.button("💾 Guardar cambios", key=f"save_{seccion}_{mes}"):
                db.guardar_seccion(mes, seccion, editado)
                st.session_state.pop(f"editor_{seccion}_{mes}", None)
                st.success(f"{singular.capitalize()} actualizado.")
                st.rerun()
