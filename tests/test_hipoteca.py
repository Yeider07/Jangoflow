"""Tests del simulador hipotecario (amortización francesa, funciones puras)."""

import pytest

from finanzas.hipoteca import amortizar, cuota_fija, tasa_mensual_desde_ea


# --------------------------------------------------------------------------- #
# tasa_mensual_desde_ea: EA -> tasa mensual equivalente
# --------------------------------------------------------------------------- #
def test_tasa_mensual_cero():
    assert tasa_mensual_desde_ea(0) == 0


def test_tasa_mensual_compone_a_la_ea():
    # (1 + i_mensual)^12 debe reconstruir (1 + EA)
    ea = 0.11
    i = tasa_mensual_desde_ea(ea)
    assert (1 + i) ** 12 == pytest.approx(1 + ea)


# --------------------------------------------------------------------------- #
# cuota_fija: cuota mensual del sistema francés
# --------------------------------------------------------------------------- #
def test_cuota_sin_interes_es_reparto_simple():
    assert cuota_fija(1200, 0, 12) == pytest.approx(100)


def test_cuota_plazo_invalido_es_cero():
    assert cuota_fija(1000, 0.02, 0) == 0.0
    assert cuota_fija(1000, 0.02, -5) == 0.0


def test_cuota_valor_conocido():
    # 1.000.000 al 1% mensual a 12 meses ≈ 88.849 (fórmula francesa)
    assert cuota_fija(1_000_000, 0.01, 12) == pytest.approx(88_848.79, abs=1)


# --------------------------------------------------------------------------- #
# amortizar: sin abonos extra
# --------------------------------------------------------------------------- #
def test_amortizar_sin_abonos_dura_el_plazo_y_salda():
    P, ea, n = 100_000_000, 0.11, 240
    cuota, filas, total_int, meses, extra = amortizar(P, ea, n)
    assert meses == n
    assert len(filas) == n
    assert filas[-1]["Saldo"] == pytest.approx(0, abs=0.01)
    assert total_int > 0
    assert extra == pytest.approx(0, abs=1e-6)  # sin abonos, salvo epsilon flotante


def test_amortizar_capital_suma_el_prestamo():
    P, ea, n = 100_000_000, 0.11, 240
    _, filas, _, _, _ = amortizar(P, ea, n)
    suma_capital = sum(f["Capital"] for f in filas)
    assert suma_capital == pytest.approx(P, rel=1e-6)


# --------------------------------------------------------------------------- #
# amortizar: con abonos a capital
# --------------------------------------------------------------------------- #
def test_abono_mensual_acorta_plazo_y_baja_intereses():
    P, ea, n = 100_000_000, 0.11, 240
    _, _, int_base, meses_base, _ = amortizar(P, ea, n)
    _, _, int_ab, meses_ab, total_extra = amortizar(
        P, ea, n, abono_mensual=500_000)
    assert meses_ab < meses_base
    assert int_ab < int_base
    assert total_extra > 0


def test_modo_calendario_agrega_columna_fecha():
    _, filas, _, _, _ = amortizar(
        50_000_000, 0.10, 60, inicio_anio=2026, inicio_mes=6)
    assert "Fecha" in filas[0]
    assert filas[0]["Fecha"] == "jun-26"


def test_sin_calendario_no_hay_fecha():
    _, filas, _, _, _ = amortizar(50_000_000, 0.10, 60)
    assert "Fecha" not in filas[0]
