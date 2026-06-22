"""Constantes y configuración del Gestor de Finanzas (sin dependencias)."""

from pathlib import Path

# La base de datos vive en la raíz del proyecto (junto a app_finanzas.py).
DB_PATH = Path(__file__).resolve().parent.parent / "finanzas.db"

# Respaldos automáticos: un archivo por día en backups/, conservando los
# últimos MAX_BACKUPS (rotación). Se crean al iniciar la app (ver db.init_db).
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
MAX_BACKUPS = 30

# Meses abreviados y completos (para etiquetas y selectores)
MESES_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}
MESES_NOMBRE = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre",
    12: "diciembre",
}

# Gastos mensuales fijos que se precargan al crear un mes nuevo desde cero.
GASTOS_PREDEFINIDOS = [
    {"nombre": "Adiciones moto",   "presupuesto": 150000},
    {"nombre": "Parqueadero Casa", "presupuesto": 50000},
    {"nombre": "Plan de datos",    "presupuesto": 44000},
    {"nombre": "Comida perra",     "presupuesto": 50000},
    {"nombre": "Factura PDA",      "presupuesto": 50000},
]

# Secciones por mes (tabla `items`) y las columnas que el usuario edita en cada una
SECCIONES = {
    # ingreso: real = el monto recibido (fijo, sin presupuesto)
    "ingreso":      ["nombre", "fecha", "real"],
    "compra_libre": ["nombre", "fecha", "real"],
    "gasto":        ["nombre", "presupuesto", "real"],
    # ahorro: real = lo que ahorraste ESE mes (aporte mensual, líquido)
    "ahorro":       ["nombre", "real"],
    # invertido: real = lo que invertiste ESE mes (aporte mensual, no líquido)
    "invertido":    ["nombre", "real"],
    # deuda: total = deuda completa, presupuesto = cuota mensual, real = pagado
    "deuda":        ["nombre", "total", "presupuesto", "real"],
}

# Tablas globales (no van por mes)
# prestamos: persona = nombre de la persona; nombre = descripción de lo prestado
PRESTAMOS_COLS = ["persona", "nombre", "fecha", "total", "devuelto"]
TARJETA_COLS = ["concepto", "persona", "fecha", "total", "cuotas", "pagado"]

# Paleta de colores de las gráficas
COLORES = {
    "primario": "#2E86AB",
    "exito": "#4ECDC4",
    "peligro": "#FF6B6B",
    "acento": "#A23B72",
    "invertido": "#F18F01",
    "gris": "#B0B0B0",
}
PALETA_AHORROS = ["#4ECDC4", "#2E86AB", "#A23B72", "#F18F01",
                  "#96CEB4", "#45B7D1", "#FFEAA7", "#C73E1D"]
