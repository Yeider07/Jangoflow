"""Tests de las utilidades de formato (funciones puras)."""

import math

import pytest

import datetime as dt

from finanzas.formato import (
    etiqueta_mes, fecha_larga, mes_por_defecto, mes_titulo, meses_a_texto, num,
    pesos, sumar_meses,
)


# --------------------------------------------------------------------------- #
# num: conversión segura a float
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("entrada, esperado", [
    (5, 5.0),
    (3.5, 3.5),
    ("12", 12.0),
    ("12.5", 12.5),
    ("", 0.0),
    (None, 0.0),
    ("abc", 0.0),
    (float("nan"), 0.0),
])
def test_num(entrada, esperado):
    assert num(entrada) == esperado


def test_num_devuelve_float():
    assert isinstance(num(7), float)


# --------------------------------------------------------------------------- #
# pesos: formato de moneda colombiano
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("valor, esperado", [
    (0, "$0"),
    (1000, "$1.000"),
    (1234567, "$1.234.567"),
    (1234.9, "$1.235"),          # redondea sin decimales
])
def test_pesos(valor, esperado):
    assert pesos(valor) == esperado


# --------------------------------------------------------------------------- #
# etiqueta_mes: 'YYYY-MM' -> 'mmm-AA'
# --------------------------------------------------------------------------- #
def test_etiqueta_mes_normal():
    assert etiqueta_mes("2025-06") == "jun-25"
    assert etiqueta_mes("2026-12") == "dic-26"


def test_etiqueta_mes_invalido_devuelve_entrada():
    assert etiqueta_mes("texto-malo") == "texto-malo"


# --------------------------------------------------------------------------- #
# meses_a_texto: nº de meses -> "X años Y meses"
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("meses, esperado", [
    (0, "0 meses"),
    (1, "1 mes"),
    (2, "2 meses"),
    (12, "1 año"),
    (13, "1 año 1 mes"),
    (14, "1 año 2 meses"),
    (24, "2 años"),
    (146, "12 años 2 meses"),
])
def test_meses_a_texto(meses, esperado):
    assert meses_a_texto(meses) == esperado


# --------------------------------------------------------------------------- #
# sumar_meses: (año, mes) + offset
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("anio, mes, offset, esperado", [
    (2025, 6, 0, (2025, 6)),
    (2025, 6, 12, (2026, 6)),
    (2025, 12, 1, (2026, 1)),
    (2025, 1, 13, (2026, 2)),
    (2026, 6, 7, (2027, 1)),
])
def test_sumar_meses(anio, mes, offset, esperado):
    assert sumar_meses(anio, mes, offset) == esperado


# --------------------------------------------------------------------------- #
# fecha_larga: (año, mes) -> "mes de año"
# --------------------------------------------------------------------------- #
def test_fecha_larga():
    assert fecha_larga(2034, 2) == "febrero de 2034"
    assert fecha_larga(2026, 6) == "junio de 2026"


# --------------------------------------------------------------------------- #
# mes_por_defecto: hoy -> mes calendario anterior 'YYYY-MM' (pago mes vencido)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("hoy, esperado", [
    (dt.date(2026, 6, 21), "2026-05"),   # caso del usuario: jun -> may
    (dt.date(2026, 1, 5), "2025-12"),    # enero retrocede de año
    (dt.date(2026, 12, 31), "2026-11"),
    (dt.date(2026, 3, 1), "2026-02"),
])
def test_mes_por_defecto(hoy, esperado):
    assert mes_por_defecto(hoy) == esperado


# --------------------------------------------------------------------------- #
# mes_titulo: 'YYYY-MM' -> 'Mes Año'
# --------------------------------------------------------------------------- #
def test_mes_titulo():
    assert mes_titulo("2026-05") == "Mayo 2026"
    assert mes_titulo("2026-12") == "Diciembre 2026"
    assert mes_titulo("basura") == "basura"
