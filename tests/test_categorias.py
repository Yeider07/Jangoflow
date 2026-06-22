"""Tests de la categorización automática de gastos (descripciones reales)."""

import pytest

from finanzas.categorias import OTROS, categorizar, color, emoji, etiqueta


@pytest.mark.parametrize("descripcion, categoria", [
    # Alimentación (varias descripciones -> una categoría)
    ("Almuerzo empresa", "Alimentación"),
    ("Coca almuerzo", "Alimentación"),
    ("Almuerzo y desayuno Empresa", "Alimentación"),
    ("Salchipapa", "Alimentación"),
    ("Comida fin de semana", "Alimentación"),
    ("Compra Ara", "Alimentación"),
    ("Cubeta de huevos", "Alimentación"),
    # Mascota gana a Alimentación pese a contener "Comida"
    ("Comida perra", "Mascota"),
    # Transporte / moto
    ("Adiciones moto", "Transporte"),
    ("Parqueadero", "Transporte"),
    ("Comparendo", "Transporte"),
    # Suscripciones
    ("Claude", "Suscripciones"),
    ("Game pass", "Suscripciones"),
    ("Plan de datos", "Suscripciones"),
    ("Internet", "Suscripciones"),
    # Servicios / vivienda
    ("Factura PDA", "Servicios"),
    ("Porteria", "Servicios"),
    # Ocio
    ("Futbol cancha", "Ocio"),
    ("Aguardiente Julian", "Ocio"),
    ("Polas", "Ocio"),
    ("Pegatina Panini", "Ocio"),
    # Regalos
    ("Dia del padre", "Regalos"),
    # Deudas
    ("Tarjeta", "Deudas"),
    ("Deuda Julian", "Deudas"),
    # Sin coincidencia -> Otros
    ("Gastos Varios", OTROS),
    ("Desbalance", OTROS),
    ("Glim gasto", OTROS),
    ("", OTROS),
])
def test_categorizar_datos_reales(descripcion, categoria):
    assert categorizar(descripcion) == categoria


def test_insensible_a_mayusculas_y_tildes():
    assert categorizar("ALMUERZO") == "Alimentación"
    assert categorizar("Adición moto") == "Transporte"  # tilde en 'adición'


def test_helpers_emoji_color_etiqueta():
    assert emoji("Mascota") == "🐶"
    assert color("Mascota").startswith("#")
    assert etiqueta("Mascota") == "🐶 Mascota"
    # Categoría desconocida cae en valores de respaldo
    assert emoji("Inexistente") == "📦"
    assert color("Inexistente").startswith("#")
