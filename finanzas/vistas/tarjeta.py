"""Vista Tarjeta de crédito: seguimiento global aislado (no afecta finanzas)."""

import datetime as dt

import pandas as pd
import streamlit as st

from finanzas import db
from finanzas.formato import pesos

_ORDEN = ["concepto", "persona", "fecha", "total", "cuotas", "pagado",
          "pendiente"]


def _column_config():
    return {
        "concepto": st.column_config.TextColumn("Concepto", width="medium"),
        "persona": st.column_config.TextColumn("Para quién / usó"),
        "fecha": st.column_config.DateColumn(
            "Fecha", format="DD-MM-YYYY", default=dt.date.today()),
        "total": st.column_config.NumberColumn(
            "Monto total", format="localized", min_value=0),
        "cuotas": st.column_config.NumberColumn("N° cuotas", min_value=1, step=1),
        "pagado": st.column_config.NumberColumn(
            "Pagado", format="localized", min_value=0),
        "pendiente": st.column_config.NumberColumn(
            "Pendiente", format="localized", disabled=True),
    }


def render():
    st.markdown(
        "<h1 style='margin-bottom:0'>💳 Tarjeta de crédito</h1>"
        "<p style='color:#888;margin-top:0'>Seguimiento independiente de "
        "compras y diferidos.</p>", unsafe_allow_html=True)
    st.caption(
        "Sección **aparte** de tus finanzas (no afecta disponible ni "
        "patrimonio). Úsala para llevar el control de lo que compras o prestas "
        "con la tarjeta, sobre todo si lo difieres a cuotas. **Pagado**: lo que "
        "ya abonaste de esa compra.")

    df = db.cargar_tarjeta()
    df["pendiente"] = df["total"] - df["pagado"]
    pagada = (df["total"] > 0) & (df["pagado"] >= df["total"])
    df_act = df[~pagada].reset_index(drop=True)
    df_pag = df[pagada].reset_index(drop=True)
    cfg = _column_config()

    st.markdown("**Compras activas (pendientes por pagar)**")
    ed_act = st.data_editor(
        df_act, key="ed_tarjeta_act", num_rows="dynamic",
        width="stretch", hide_index=True,
        column_config=cfg, column_order=_ORDEN)

    with st.expander(f"✅ Compras ya pagadas ({len(df_pag)})", expanded=False):
        if df_pag.empty:
            st.caption("Aún no hay compras pagadas.")
            ed_pag = df_pag
        else:
            ed_pag = st.data_editor(
                df_pag, key="ed_tarjeta_pag", num_rows="dynamic",
                width="stretch", hide_index=True,
                column_config=cfg, column_order=_ORDEN)

    if st.button("💾 Guardar tarjeta"):
        combinado = pd.concat([ed_act, ed_pag], ignore_index=True)
        db.guardar_tarjeta(combinado.drop(columns=["pendiente"], errors="ignore"))
        st.session_state.pop("ed_tarjeta_act", None)
        st.session_state.pop("ed_tarjeta_pag", None)
        st.success("Tarjeta guardada.")
        st.rerun()

    todo = pd.concat([ed_act, ed_pag], ignore_index=True)
    if not todo.empty:
        tt = float(pd.to_numeric(todo["total"], errors="coerce").sum())
        tp = float(pd.to_numeric(todo["pagado"], errors="coerce").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Total en tarjeta", pesos(tt))
        c2.metric("Pagado", pesos(tp))
        c3.metric("Pendiente por pagar", pesos(tt - tp))

    st.info("💡 Esto es solo seguimiento. El gasto real de la tarjeta lo sigues "
            "registrando en **Finanzas → Deudas** como ya lo haces. Las compras "
            "pagadas se ocultan arriba para no llenar la vista.")
