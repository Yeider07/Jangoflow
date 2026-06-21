"""
Gestor de Finanzas Personales — punto de entrada (Streamlit).

Este archivo es delgado: solo configura la página, inicializa la base de datos
y enruta a la vista correspondiente. La lógica vive en el paquete `finanzas/`:

    finanzas/config.py    -> constantes y rutas
    finanzas/formato.py   -> utilidades de formato
    finanzas/db.py        -> acceso a SQLite (conexión, migraciones, CRUD)
    finanzas/reportes.py  -> cálculos y agregaciones
    finanzas/hipoteca.py  -> simulador de crédito
    finanzas/vistas/      -> capa de presentación (una vista por archivo)

Ejecutar:  .venv/bin/streamlit run app_finanzas.py
"""

import streamlit as st

from finanzas import db
from finanzas.formato import etiqueta_mes
from finanzas.vistas import (
    dashboard, general, hipotecario, historico, metas, prestado, sidebar,
    tarjeta, registrar,
)

st.set_page_config(page_title="Gestor de Finanzas", page_icon="💰",
                   layout="wide")
db.init_db()

vista = sidebar.seleccionar_vista()

# --- Vistas aisladas (no usan el flujo de meses) ---
if vista == sidebar.VISTA_TARJETA:
    tarjeta.render()
elif vista == sidebar.VISTA_HIPOTECARIO:
    hipotecario.render()

# --- Vista principal: Finanzas (por mes, con pestañas) ---
else:
    mes = sidebar.gestionar_meses()

    st.markdown(
        f"<h1 style='margin-bottom:0'>Gestor de Finanzas</h1>"
        f"<p style='color:#888;margin-top:0'>Mes activo: "
        f"<b>{etiqueta_mes(mes)}</b></p>",
        unsafe_allow_html=True,
    )

    t_general, t_dash, t_edit, t_metas, t_prestado, t_hist = st.tabs(
        ["🌎 General", "📊 Dashboard", "✏️ Registrar / Editar",
         "🎯 Metas", "🤝 Prestado", "📈 Histórico"])

    with t_general:
        general.render()
    with t_dash:
        dashboard.render(mes)
    with t_edit:
        registrar.render(mes)
    with t_metas:
        metas.render()
    with t_prestado:
        prestado.render()
    with t_hist:
        historico.render()
