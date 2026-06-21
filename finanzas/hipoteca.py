"""Lógica del simulador de crédito hipotecario (amortización francesa).

Sin Streamlit ni base de datos: funciones puras y testeables.
"""

from finanzas.config import MESES_ES
from finanzas.formato import sumar_meses


def tasa_mensual_desde_ea(ea):
    """Tasa efectiva anual (fracción) -> tasa mensual equivalente."""
    return (1 + ea) ** (1 / 12) - 1


def cuota_fija(P, i, n):
    """Cuota mensual fija de un crédito (sistema francés)."""
    if n <= 0:
        return 0.0
    if i == 0:
        return P / n
    return P * i / (1 - (1 + i) ** -n)


def amortizar(P, ea, n, abono_mensual=0.0, arriendo=0.0, arriendo_meses=0,
              prima=0.0, prima_mes=6, cesantias=0.0, cesantias_mes=2,
              inicio_anio=None, inicio_mes=None):
    """Genera la tabla de amortización con abonos extra a capital.

    - abono_mensual: pago adicional fijo cada mes.
    - arriendo: ingreso mensual extra a capital durante 'arriendo_meses' meses.
    - prima / cesantias: montos anuales abonados en su mes (prima_mes,
      cesantias_mes). Si no se da fecha de inicio, se abonan cada 12 meses.
    - inicio_anio/inicio_mes: si se dan, la tabla usa el calendario real.

    Devuelve (cuota, filas, total_intereses, meses_reales, total_abonado_extra).
    """
    i = tasa_mensual_desde_ea(ea)
    cuota = cuota_fija(P, i, n)
    filas, saldo, total_int, mes, total_extra = [], float(P), 0.0, 0, 0.0
    usar_calendario = bool(inicio_anio and inicio_mes)
    tope = n + 2000  # seguridad anti-bucle

    while saldo > 0.01 and mes < tope:
        mes += 1
        if usar_calendario:
            anio_cal, mes_cal = sumar_meses(inicio_anio, inicio_mes, mes - 1)
        else:
            anio_cal, mes_cal = None, None

        interes = saldo * i
        extra = abono_mensual
        if arriendo_meses and mes <= arriendo_meses:
            extra += arriendo
        if usar_calendario:
            if prima and mes_cal == prima_mes:
                extra += prima
            if cesantias and mes_cal == cesantias_mes:
                extra += cesantias
        elif mes % 12 == 0:               # sin fecha: cada 12 meses
            extra += prima + cesantias

        capital = cuota - interes + extra
        if capital >= saldo:              # último pago
            capital = saldo
        pago = interes + capital
        total_extra += max(pago - cuota, 0.0)
        saldo -= capital
        total_int += interes

        fila = {"No.": mes, "Cuota": pago, "Intereses": interes,
                "Capital": capital, "Saldo": max(saldo, 0.0)}
        if usar_calendario:
            fila["Fecha"] = f"{MESES_ES[mes_cal]}-{str(anio_cal)[2:]}"
        filas.append(fila)

    return cuota, filas, total_int, mes, total_extra
