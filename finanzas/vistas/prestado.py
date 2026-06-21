"""Vista Prestado: lista global de dinero prestado (activos + ya pagados)."""

import datetime as dt

import pandas as pd
import streamlit as st

from finanzas import db
from finanzas.formato import pesos

_ORDEN = ["persona", "nombre", "fecha", "total", "devuelto", "pendiente"]


def _column_config():
    return {
        "persona": st.column_config.TextColumn("Persona", width="medium"),
        "nombre": st.column_config.TextColumn("Descripción", width="medium"),
        "fecha": st.column_config.DateColumn(
            "Fecha", format="DD-MM-YYYY", default=dt.date.today()),
        "total": st.column_config.NumberColumn(
            "Total prestado", format="localized", min_value=0),
        "devuelto": st.column_config.NumberColumn(
            "Devuelto", format="localized", min_value=0),
        "pendiente": st.column_config.NumberColumn(
            "Pendiente", format="localized", disabled=True),
    }


def render():
    st.subheader("🤝 Dinero prestado (global)")
    st.caption(
        "Esta sección NO va por mes: es tu lista global de préstamos, vive "
        "hasta que te paguen. **Total prestado**: cuánto le prestaste a cada "
        "quien. **Devuelto**: lo que ya te han devuelto. El pendiente por "
        "cobrar se descuenta de tu ahorro líquido en el General.")

    df = db.cargar_prestamos()
    df["pendiente"] = df["total"] - df["devuelto"]
    pagado = (df["total"] > 0) & (df["devuelto"] >= df["total"])
    df_act = df[~pagado].reset_index(drop=True)
    df_pag = df[pagado].reset_index(drop=True)
    cfg = _column_config()

    st.markdown("**Préstamos activos (aún te deben)**")
    ed_act = st.data_editor(
        df_act, key="ed_prest_act", num_rows="dynamic",
        width="stretch", hide_index=True,
        column_config=cfg, column_order=_ORDEN)

    with st.expander(f"✅ Préstamos ya pagados ({len(df_pag)})", expanded=False):
        if df_pag.empty:
            st.caption("Aún no hay préstamos pagados.")
            ed_pag = df_pag
        else:
            ed_pag = st.data_editor(
                df_pag, key="ed_prest_pag", num_rows="dynamic",
                width="stretch", hide_index=True,
                column_config=cfg, column_order=_ORDEN)

    editado = pd.concat([ed_act, ed_pag], ignore_index=True)

    if not editado.empty:
        tot_t = float(pd.to_numeric(editado["total"], errors="coerce").sum())
        tot_d = float(pd.to_numeric(editado["devuelto"], errors="coerce").sum())
        c1, c2, c3 = st.columns(3)
        c1.caption(f"Total prestado: **{pesos(tot_t)}**")
        c2.caption(f"Devuelto: **{pesos(tot_d)}**")
        c3.caption(f"Por cobrar: **{pesos(tot_t - tot_d)}**")

    if st.button("💾 Guardar préstamos"):
        db.guardar_prestamos(editado.drop(columns=["pendiente"], errors="ignore"))
        st.session_state.pop("ed_prest_act", None)
        st.session_state.pop("ed_prest_pag", None)
        st.success("Préstamos guardados.")
        st.rerun()

    st.info("💡 Cuando te devuelvan, sube el **Devuelto**. Al quedar Devuelto = "
            "Total prestado, el préstamo se mueve solo a **✅ Ya pagados** y "
            "desaparece de esta lista.")

    _resumen_por_persona(editado)


def _resumen_por_persona(editado):
    st.divider()
    st.subheader("🔍 Resumen por persona")
    df = editado.copy()
    df["persona"] = (df["persona"].astype(str).str.strip()
                     .replace("", "(sin nombre)"))
    df["nombre"] = df["nombre"].astype(str).fillna("")
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    df["devuelto"] = pd.to_numeric(df["devuelto"], errors="coerce").fillna(0)
    df = df[(df["total"] != 0) | (df["devuelto"] != 0)]

    if df.empty:
        st.caption("Aún no hay préstamos para resumir.")
        return

    personas = sorted(df["persona"].unique())
    sel = st.selectbox("Filtrar por persona", ["Todos"] + personas)
    df_f = df if sel == "Todos" else df[df["persona"] == sel]

    t_total = float(df_f["total"].sum())
    t_dev = float(df_f["devuelto"].sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Total prestado", pesos(t_total))
    m2.metric("Total abonado", pesos(t_dev))
    m3.metric("Debe (pendiente)", pesos(t_total - t_dev))

    det = df_f.copy()
    det["pendiente"] = det["total"] - det["devuelto"]
    det = det[["persona", "nombre", "total", "devuelto", "pendiente"]]
    det.columns = ["Persona", "Descripción", "Total", "Abonado", "Debe"]
    st.dataframe(
        det.style.format({"Total": pesos, "Abonado": pesos, "Debe": pesos}),
        width="stretch", hide_index=True)

    st.caption("Totales por persona:")
    grp = df.groupby("persona", as_index=False).agg(
        Total=("total", "sum"), Abonado=("devuelto", "sum"))
    grp["Debe"] = grp["Total"] - grp["Abonado"]
    grp = grp.rename(columns={"persona": "Persona"}).sort_values(
        "Debe", ascending=False)
    st.dataframe(
        grp.style.format({"Total": pesos, "Abonado": pesos, "Debe": pesos}),
        width="stretch", hide_index=True)
