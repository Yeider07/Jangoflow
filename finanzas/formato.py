"""Utilidades de formato y conversión (sin dependencias de datos ni Streamlit)."""

from finanzas.config import MESES_ES, MESES_NOMBRE


def num(v):
    """Convierte cualquier valor a float de forma segura. Vacío, None o NaN
    se vuelven 0.0 (evita errores con celdas vacías del editor)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if f != f else f   # f != f detecta NaN


def pesos(valor):
    """Formato de moneda estilo colombiano: $1.234.567"""
    return "$" + f"{valor:,.0f}".replace(",", ".")


def etiqueta_mes(mes):
    """'2025-06' -> 'jun-25'"""
    try:
        a, m = mes.split("-")
        return f"{MESES_ES[int(m)]}-{a[2:]}"
    except Exception:
        return mes


def meses_a_texto(m):
    """144 -> '12 años' / 146 -> '12 años 2 meses'"""
    m = int(round(m))
    a, r = divmod(m, 12)
    partes = []
    if a:
        partes.append(f"{a} año" + ("s" if a != 1 else ""))
    if r:
        partes.append(f"{r} mes" + ("es" if r != 1 else ""))
    return " ".join(partes) if partes else "0 meses"


def sumar_meses(anio, mes, offset):
    """(anio, mes) + offset meses -> (anio, mes)."""
    idx = (mes - 1) + offset
    return anio + idx // 12, idx % 12 + 1


def fecha_larga(anio, mes):
    """(2034, 2) -> 'febrero de 2034'"""
    return f"{MESES_NOMBRE[mes]} de {anio}"
