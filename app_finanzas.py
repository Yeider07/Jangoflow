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
from finanzas.formato import mes_titulo
from finanzas.vistas import (
    dashboard, general, hipotecario, historico, prestado, sidebar,
    tarjeta, registrar,
)

st.set_page_config(page_title="Gestor de Finanzas", page_icon="💰",
                   layout="wide")

# CSS global: cabecera tipo tarjeta + métricas responsive (2 por fila en móvil).
st.markdown(
    """
    <style>
    /* Cabecera: tarjeta con el título y el mes activo como píldora. */
    .app-header {
        display: flex; align-items: center; justify-content: space-between;
        gap: 1rem;
        background: linear-gradient(135deg, #1B2230 0%, #141925 100%);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 1.05rem 1.35rem;
        margin: 0.2rem 0 0.9rem;
    }
    .app-title { font-size: 1.55rem; font-weight: 700; line-height: 1.1; }
    .app-sub { font-size: 0.78rem; opacity: 0.5; margin-top: 0.2rem; }
    .app-month {
        display: flex; flex-direction: column; align-items: flex-end;
        background: rgba(63,201,176,0.12);
        border: 1px solid rgba(63,201,176,0.40);
        border-radius: 12px; padding: 0.45rem 0.85rem; white-space: nowrap;
    }
    .app-month-label {
        font-size: 0.6rem; letter-spacing: 0.09em; text-transform: uppercase;
        opacity: 0.6;
    }
    .app-month-value { font-size: 1.1rem; font-weight: 600; color: #3FC9B0; }

    /* --- Tarjetas glass (st.container con key 'dashcard_*') --- */
    [class*="st-key-dashcard"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 0.6rem 1.2rem 1rem !important;
        margin-bottom: 0.5rem;
        backdrop-filter: blur(13px);
        -webkit-backdrop-filter: blur(13px);
        box-shadow: 0 16px 44px rgba(0,0,0,0.45),
                    inset 0 1px 0 rgba(255,255,255,0.06);
    }
    /* Título dentro de cada tarjeta con acento menta (subheader h3 o md h5) */
    [class*="st-key-dashcard"] :is(h3, h4, h5) {
        border-left: 3px solid #3FC9B0;
        padding-left: 0.55rem;
        margin: 0.2rem 0 0.6rem;
    }

    /* Etiqueta de sección (grupo de tarjetas), tipo chip menta. */
    .dash-section {
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: #3FC9B0; opacity: 0.9;
        margin: 0.4rem 0 0.55rem;
    }

    /* --- KPIs como mini-tarjetas glass --- */
    .kpis {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.7rem;
        margin: 0.2rem 0 0.6rem;
    }
    .kpis .kpi {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 0.85rem 1rem;
        backdrop-filter: blur(11px);
        -webkit-backdrop-filter: blur(11px);
        box-shadow: 0 10px 28px rgba(0,0,0,0.38),
                    inset 0 1px 0 rgba(255,255,255,0.06);
    }
    .kpis .kpi-label {
        font-size: 0.68rem; letter-spacing: 0.06em; text-transform: uppercase;
        opacity: 0.55; margin-bottom: 0.25rem;
    }
    .kpis .kpi-value { font-weight: 500; font-size: 1.55rem; line-height: 1.15;
                       white-space: nowrap; }
    .kpis .kpi-delta { font-size: 0.76rem; margin-top: 0.2rem; }
    .kpis .kpi-delta.pos { color: #5FC97B; }
    .kpis .kpi-delta.neg { color: #F2607A; }

    /* Métricas: 2 por fila en móvil (no una columna larga). */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
            flex-wrap: wrap !important;
        }
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
            > [data-testid="stColumn"] {
            flex: 1 1 calc(50% - 0.6rem) !important;
            min-width: calc(50% - 0.6rem) !important;
            width: auto !important;
        }
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .app-header { padding: 0.85rem 1rem; border-radius: 14px; }
        .app-title { font-size: 1.2rem; }
        .app-month-value { font-size: 0.95rem; }
        .kpis { grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }
        .kpis .kpi-value { font-size: 1.3rem; }
        .kpis .kpi { padding: 0.65rem 0.75rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        f"""
        <div class="app-header">
          <div>
            <div class="app-title">💰 Gestor de Finanzas</div>
            <div class="app-sub">Tus finanzas personales, mes a mes</div>
          </div>
          <div class="app-month">
            <span class="app-month-label">Mes activo</span>
            <span class="app-month-value">{mes_titulo(mes)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t_general, t_dash, t_edit, t_prestado, t_hist = st.tabs(
        ["🌎 General", "📊 Dashboard", "✏️ Registrar / Editar",
         "🤝 Prestado", "📈 Histórico"])

    with t_general:
        general.render()
    with t_dash:
        dashboard.render(mes)
    with t_edit:
        registrar.render(mes)
    with t_prestado:
        prestado.render()
    with t_hist:
        historico.render()
