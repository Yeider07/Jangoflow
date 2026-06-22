"""Categorización automática de gastos a partir de su descripción.

El usuario escribe descripciones libres ("Almuerzo empresa", "Coca almuerzo",
"Salchipapa"...) que en realidad pertenecen a una misma categoría
(Alimentación). Aquí se mapea cada descripción a una categoría mediante
palabras clave, sin tocar la base de datos: la categoría se calcula al vuelo.

Para afinarlo: agrega palabras clave (stems, en minúscula y sin tildes) a la
categoría correspondiente en CATEGORIAS. El orden importa — la primera
categoría cuya palabra clave aparezca en la descripción gana, así que las más
específicas van primero (p. ej. Mascota antes que Alimentación para que
"Comida perra" sea Mascota y no Alimentación).
"""

import unicodedata

OTROS = "Otros"

# (categoría, emoji, color vivo, [palabras clave en minúscula sin tildes])
CATEGORIAS = [
    ("Mascota", "🐶", "#5FC97B",
     ["perr", "mascota", "veterinari", "gato", "purina"]),
    ("Transporte", "🏍️", "#4C9BE0",
     ["moto", "adicion", "parqueader", "gasolin", "comparend", "taxi", "uber",
      "didi", "peaje", "soat", "tecnomecanic", " bus ", "pasaje", "llanta"]),
    ("Suscripciones", "🎮", "#B07BE8",
     ["claude", "game pass", "gamepass", "plan de datos", "internet", "netflix",
      "spotify", "disney", "youtube", "hbo", " max ", "suscrip", "chatgpt"]),
    ("Servicios", "🏠", "#3FC9C0",
     ["servicio", "porteria", "factura", "pda", "arriendo", "administracion",
      " agua ", " luz ", "energia", " gas ", "predial", "epm"]),
    ("Deudas", "💳", "#D98E5A",
     ["deuda", "prestamo", "tarjeta", "cuota", "credito"]),
    ("Regalos", "🎁", "#E8C84D",
     ["regalo", "dia del padre", "dia de la madre", "cumple", "navidad",
      "aguinaldo", "detalle"]),
    ("Ocio", "🍻", "#F2607A",
     ["futbol", "cancha", "aguardiente", "pola", "cerveza", "trago", "licor",
      "salida", "fiesta", "rumba", "pegatina", "panini", "cine", "carta",
      "lectura", "juego", "viaje"]),
    ("Alimentación", "🍔", "#F2A93B",
     ["almuerz", "desayun", "cena", "comida", "salchip", "tinto", "huevo",
      "mercado", "merca", "supermercado", " ara ", "tienda", "restaurante",
      "coca", "mecato", "pan ", "fruta", "domicilio", "rappi", "cafe"]),
]

# Color de respaldo para "Otros" / categoría sin definir.
COLOR_OTROS = "#9AA0AA"

_EMOJI = {c: e for c, e, _, _ in CATEGORIAS}
_EMOJI[OTROS] = "📦"
_COLOR = {c: col for c, _, col, _ in CATEGORIAS}
_COLOR[OTROS] = COLOR_OTROS


def _normalizar(texto):
    """A minúsculas, sin tildes, con espacios a los lados (para matches)."""
    t = (texto or "").lower().strip()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return f" {t} "


def categorizar(nombre):
    """Descripción libre -> nombre de categoría (OTROS si no encaja)."""
    t = _normalizar(nombre)
    for categoria, _emoji, _color, claves in CATEGORIAS:
        if any(clave in t for clave in claves):
            return categoria
    return OTROS


def emoji(categoria):
    """Emoji asociado a una categoría."""
    return _EMOJI.get(categoria, "📦")


def color(categoria):
    """Color (hex) asociado a una categoría."""
    return _COLOR.get(categoria, COLOR_OTROS)


def etiqueta(categoria):
    """'Alimentación' -> '🍔 Alimentación' (para mostrar en gráficos)."""
    return f"{emoji(categoria)} {categoria}"
