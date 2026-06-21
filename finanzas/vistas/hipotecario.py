"""Vista Crédito hipotecario: simulador de amortización con abonos a capital."""

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finanzas.config import COLORES, MESES_NOMBRE
from finanzas.formato import fecha_larga, meses_a_texto, pesos, sumar_meses
from finanzas.hipoteca import amortizar
from finanzas.vistas.componentes import input_pesos


def _entradas():
    """Renderiza los inputs y devuelve un dict con los parámetros."""
    st.subheader("Datos del crédito")
    f1, f2, f3 = st.columns(3)
    with f1:
        vivienda = input_pesos("Valor de la vivienda", "hip_vivienda", 205_000_000)
    with f2:
        inicial = input_pesos("Cuota inicial", "hip_inicial", 41_000_000)
    deuda = max(vivienda - inicial, 0)
    f3.metric("Valor a financiar (deuda)", pesos(deuda))

    g1, g2, g3 = st.columns(3)
    fecha_inicio = g1.date_input(
        "📆 Fecha de inicio del crédito", value=dt.date.today(),
        help="Mes en que empiezas a pagar. Define cuándo caen prima/cesantías "
             "y el mes de finalización.")
    plazo_anios = g2.number_input("Plazo (años)", 1, 40, 20, step=1)
    tasa_ea = g3.number_input(
        "Tasa de interés efectiva anual (%)", 0.0, 60.0, 11.0, step=0.1) / 100

    st.subheader("Abonos extra (opcionales)")
    st.caption("Todo esto se abona a capital y acelera el pago del crédito.")
    n_meses = int(plazo_anios) * 12
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        abono = input_pesos("💵 Abono mensual fijo", "hip_abono", 0,
                            help="Pago adicional fijo cada mes, a capital.")
    with e2:
        arriendo = input_pesos("🏘️ Arriendo mensual", "hip_arriendo", 700_000,
                               help="Ingreso por arrendar el apartamento.")
        arriendo_meses = st.number_input(
            "Meses que arriendas", 0, n_meses, 12, step=1)
    with e3:
        prima = input_pesos("🎁 Prima anual", "hip_prima", 0,
                            help="Se abona 1 vez al año, en el mes elegido.")
        prima_mes = st.selectbox("Mes de la prima", list(MESES_NOMBRE.keys()),
                                 index=5, format_func=lambda m: MESES_NOMBRE[m])
    with e4:
        cesantias = input_pesos("🏦 Cesantías anuales", "hip_cesantias", 0,
                               help="Se abonan 1 vez al año, en el mes elegido.")
        cesantias_mes = st.selectbox(
            "Mes de cesantías", list(MESES_NOMBRE.keys()), index=1,
            format_func=lambda m: MESES_NOMBRE[m])

    return {
        "deuda": deuda, "tasa_ea": tasa_ea, "n_meses": n_meses,
        "inicio_anio": fecha_inicio.year, "inicio_mes": fecha_inicio.month,
        "abono": abono, "arriendo": arriendo,
        "arriendo_meses": int(arriendo_meses),
        "prima": prima, "prima_mes": prima_mes,
        "cesantias": cesantias, "cesantias_mes": cesantias_mes,
    }


def render():
    st.markdown(
        "<h1 style='margin-bottom:0'>🏠 Simulador de crédito hipotecario</h1>"
        "<p style='color:#888;margin-top:0'>Simula tu cuota, la amortización y "
        "el ahorro al abonar a capital.</p>", unsafe_allow_html=True)

    p = _entradas()
    if p["deuda"] <= 0:
        st.warning("El valor a financiar debe ser mayor que 0 "
                   "(revisa vivienda y cuota inicial).")
        return

    hay_abonos = (p["abono"] > 0 or (p["arriendo"] > 0 and p["arriendo_meses"] > 0)
                  or p["prima"] > 0 or p["cesantias"] > 0)

    cuota, filas_base, int_base, meses_base, _ = amortizar(
        p["deuda"], p["tasa_ea"], p["n_meses"],
        inicio_anio=p["inicio_anio"], inicio_mes=p["inicio_mes"])
    _, filas_ab, int_ab, meses_ab, total_abonado = amortizar(
        p["deuda"], p["tasa_ea"], p["n_meses"], abono_mensual=p["abono"],
        arriendo=p["arriendo"], arriendo_meses=p["arriendo_meses"],
        prima=p["prima"], prima_mes=p["prima_mes"],
        cesantias=p["cesantias"], cesantias_mes=p["cesantias_mes"],
        inicio_anio=p["inicio_anio"], inicio_mes=p["inicio_mes"])

    ingresos_req = cuota / 0.4  # regla del 40%
    fin_base = sumar_meses(p["inicio_anio"], p["inicio_mes"], meses_base - 1)
    fin_ab = sumar_meses(p["inicio_anio"], p["inicio_mes"], meses_ab - 1)

    st.divider()
    st.subheader("Resultado")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("💵 Cuota mensual", pesos(cuota))
    r2.metric("📅 Plazo original", meses_a_texto(p["n_meses"]),
              help=f"Empieza en {fecha_larga(p['inicio_anio'], p['inicio_mes'])}.")
    r3.metric("🏁 Termina (sin abonos)", fecha_larga(*fin_base))
    r4.metric("💼 Ingresos requeridos", pesos(ingresos_req),
              help="Aproximado: la cuota no debería superar el 40% de tus "
                   "ingresos (cuota ÷ 0.4).")

    if hay_abonos:
        _impacto(p, cuota, int_base, int_ab, meses_base, meses_ab,
                 fin_base, fin_ab, total_abonado)

    _grafica_saldo(filas_base, filas_ab, hay_abonos)
    _tabla_amortizacion(filas_ab if hay_abonos else filas_base)

    st.caption("ℹ️ Simulador independiente: no afecta tus finanzas ni se guarda. "
               "Ajusta los valores para ver distintos escenarios.")


def _impacto(p, cuota, int_base, int_ab, meses_base, meses_ab,
             fin_base, fin_ab, total_abonado):
    st.divider()
    st.subheader("📉 Impacto de tus abonos a capital")
    meses_ahorrados = meses_base - meses_ab
    int_ahorrado = int_base - int_ab
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("🏁 Termina (con abonos)", fecha_larga(*fin_ab),
              delta=f"-{meses_a_texto(meses_ahorrados)}", delta_color="inverse",
              help="Mes estimado del último pago con tus abonos.")
    a2.metric("⏱️ Nuevo plazo", meses_a_texto(meses_ab))
    a3.metric("💰 Ahorro en intereses", pesos(int_ahorrado))
    a4.metric("🧾 Total intereses con abonos", pesos(int_ab))

    detalle = []
    if p["abono"] > 0:
        detalle.append(f"abono fijo de **{pesos(p['abono'])}**/mes")
    if p["arriendo"] > 0 and p["arriendo_meses"] > 0:
        detalle.append(f"arriendo de **{pesos(p['arriendo'])}**/mes por "
                       f"**{p['arriendo_meses']} meses**")
    if p["prima"] > 0:
        detalle.append(f"prima anual de **{pesos(p['prima'])}**")
    if p["cesantias"] > 0:
        detalle.append(f"cesantías anuales de **{pesos(p['cesantias'])}**")
    st.success(
        f"Con {', '.join(detalle)}, terminarías en **{fecha_larga(*fin_ab)}** "
        f"({meses_a_texto(meses_ab)}) en vez de {fecha_larga(*fin_base)} — te "
        f"ahorras **{meses_a_texto(meses_ahorrados)}** y dejas de pagar "
        f"**{pesos(int_ahorrado)}** en intereses. Abonarías "
        f"**{pesos(total_abonado)}** extra en total.")


def _grafica_saldo(filas_base, filas_ab, hay_abonos):
    st.divider()
    st.subheader("Evolución del saldo")
    df_base = pd.DataFrame(filas_base)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_base["No."], y=df_base["Saldo"], mode="lines",
        name="Sin abonos", line=dict(color=COLORES["peligro"], width=3)))
    if hay_abonos:
        df_ab = pd.DataFrame(filas_ab)
        fig.add_trace(go.Scatter(
            x=df_ab["No."], y=df_ab["Saldo"], mode="lines",
            name="Con abonos", line=dict(color=COLORES["exito"], width=3)))
    fig.update_layout(height=360, margin=dict(t=10, b=10, l=10, r=10),
                      xaxis_title="Mes", yaxis_title="Saldo",
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")


def _tabla_amortizacion(filas):
    st.subheader("Tabla de amortización")
    df = pd.DataFrame(filas)
    if "Fecha" in df.columns:
        df = df[["No.", "Fecha", "Cuota", "Intereses", "Capital", "Saldo"]]
    st.dataframe(
        df.style.format({"Cuota": pesos, "Intereses": pesos,
                         "Capital": pesos, "Saldo": pesos}),
        width="stretch", hide_index=True, height=400)
