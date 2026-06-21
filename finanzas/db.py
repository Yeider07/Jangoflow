"""Capa de acceso a datos (SQLite): conexión, migraciones y CRUD.

Toda la información se guarda en un único archivo local (config.DB_PATH).
- Tabla `items`: registros por mes (ingreso, compra_libre, gasto, ahorro,
  invertido, deuda).
- Tabla `prestamos`: dinero prestado (global, no por mes).
- Tabla `tarjeta`: seguimiento de tarjeta de crédito (global, aislado).
"""

import datetime as dt
import sqlite3

import pandas as pd

from finanzas.config import (
    DB_PATH, BACKUP_DIR, MAX_BACKUPS, SECCIONES, GASTOS_PREDEFINIDOS,
    PRESTAMOS_COLS, TARJETA_COLS, METAS_COLS,
)
from finanzas.formato import num


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def respaldar_db():
    """Crea un respaldo diario de la base (uno por día) y rota los antiguos.

    Usa la API de copia de SQLite (consistente aunque la BD esté en uso). No
    interrumpe el arranque si algo falla. Conserva los últimos MAX_BACKUPS.
    """
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        return  # nada que respaldar (primer arranque)
    BACKUP_DIR.mkdir(exist_ok=True)
    destino = BACKUP_DIR / f"finanzas-{dt.date.today():%Y%m%d}.db"
    if destino.exists():
        return  # ya existe el respaldo de hoy
    try:
        with sqlite3.connect(DB_PATH) as origen, \
                sqlite3.connect(destino) as copia:
            origen.backup(copia)
    except Exception:
        if destino.exists():
            destino.unlink(missing_ok=True)  # no dejar un respaldo a medias
        return
    # Rotación: borrar los respaldos más antiguos por encima del tope.
    respaldos = sorted(BACKUP_DIR.glob("finanzas-*.db"))
    for viejo in respaldos[:-MAX_BACKUPS]:
        viejo.unlink(missing_ok=True)


def init_db():
    """Crea las tablas si no existen y aplica las migraciones pendientes."""
    respaldar_db()  # respaldo diario antes de tocar nada
    with conectar() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                mes         TEXT NOT NULL,           -- formato 'YYYY-MM'
                seccion     TEXT NOT NULL,
                nombre      TEXT,
                fecha       TEXT,
                total       REAL DEFAULT 0,          -- total de la deuda (solo deudas)
                presupuesto REAL DEFAULT 0,          -- en deudas = cuota mensual
                real        REAL DEFAULT 0,          -- en deudas = pagado este mes
                pagado      INTEGER DEFAULT 0,
                orden       INTEGER DEFAULT 0
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS prestamos (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                persona  TEXT,               -- nombre de la persona
                nombre   TEXT,               -- descripción de lo prestado
                fecha    TEXT,
                total    REAL DEFAULT 0,     -- total prestado
                devuelto REAL DEFAULT 0,     -- devuelto acumulado
                orden    INTEGER DEFAULT 0
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS tarjeta (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                concepto TEXT,
                persona  TEXT,               -- para quién / quién usó la tarjeta
                fecha    TEXT,
                total    REAL DEFAULT 0,     -- monto de la compra
                cuotas   INTEGER DEFAULT 1,  -- número de cuotas (diferido)
                pagado   REAL DEFAULT 0,     -- abonado hasta ahora
                orden    INTEGER DEFAULT 0
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS metas (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre   TEXT,
                objetivo REAL DEFAULT 0,     -- monto que quieres alcanzar
                ahorrado REAL DEFAULT 0,     -- cuánto llevas para esta meta
                orden    INTEGER DEFAULT 0
            )
            """
        )

        # --- Migración de columnas faltantes (bases antiguas) ---
        cols = [r["name"] for r in con.execute("PRAGMA table_info(items)")]
        if "total" not in cols:
            con.execute("ALTER TABLE items ADD COLUMN total REAL DEFAULT 0")

        cols_p = [r["name"] for r in con.execute("PRAGMA table_info(prestamos)")]
        if "persona" not in cols_p:
            con.execute("ALTER TABLE prestamos ADD COLUMN persona TEXT DEFAULT ''")

        # --- Migraciones de datos (versionadas con PRAGMA user_version) ---
        version = con.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            # En deudas, el viejo 'presupuesto' guardaba el TOTAL de la deuda.
            con.execute(
                "UPDATE items SET total = presupuesto, "
                "presupuesto = (CASE WHEN real > 0 THEN real ELSE presupuesto END) "
                "WHERE seccion = 'deuda'"
            )
            con.execute("PRAGMA user_version = 1")

        if version < 2:
            # Mover 'Prestado' e 'Invertido' de Ahorros a sus propias secciones.
            con.execute(
                "UPDATE items SET seccion = 'prestado', "
                "total = (CASE WHEN presupuesto > 0 THEN presupuesto ELSE real END), "
                "presupuesto = 0, real = 0 "
                "WHERE seccion = 'ahorro' AND lower(nombre) LIKE 'prestado%'"
            )
            con.execute(
                "UPDATE items SET seccion = 'invertido', "
                "real = (CASE WHEN real > 0 THEN real ELSE presupuesto END), "
                "presupuesto = 0, total = 0 "
                "WHERE seccion = 'ahorro' AND lower(nombre) LIKE 'invertido%'"
            )
            con.execute("PRAGMA user_version = 2")

        if version < 3:
            # Mover los préstamos que estaban por mes (items) a la tabla global.
            filas = con.execute(
                "SELECT nombre, MAX(total) AS total, SUM(real) AS devuelto "
                "FROM items WHERE seccion = 'prestado' GROUP BY nombre"
            ).fetchall()
            for f in filas:
                if f["nombre"]:
                    con.execute(
                        "INSERT INTO prestamos (nombre, fecha, total, devuelto) "
                        "VALUES (?, '', ?, ?)",
                        (f["nombre"], num(f["total"]), num(f["devuelto"])),
                    )
            con.execute("DELETE FROM items WHERE seccion = 'prestado'")
            con.execute("PRAGMA user_version = 3")

        con.commit()


def _fecha_a_texto(valor):
    """Timestamp/date del editor -> texto 'YYYY-MM-DD' (o '' si está vacío)."""
    if valor is None or pd.isna(valor):
        return ""
    try:
        return pd.to_datetime(valor).strftime("%Y-%m-%d")
    except Exception:
        return str(valor)


# --------------------------------------------------------------------------- #
# Meses (tabla items)
# --------------------------------------------------------------------------- #
def listar_meses():
    """Lista de meses guardados, del más reciente al más antiguo."""
    with conectar() as con:
        filas = con.execute(
            "SELECT DISTINCT mes FROM items ORDER BY mes DESC"
        ).fetchall()
    return [f["mes"] for f in filas]


def cargar_seccion(mes, seccion):
    """DataFrame con las filas de una sección para un mes (tipos coherentes)."""
    cols = SECCIONES[seccion]
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT * FROM items WHERE mes = ? AND seccion = ? ORDER BY orden, id",
            con, params=(mes, seccion),
        )
    df = pd.DataFrame(columns=cols) if df.empty else df[cols]
    if "pagado" in df.columns:
        df["pagado"] = df["pagado"].fillna(0).astype(bool)
    for c in ("total", "presupuesto", "real"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    if "nombre" in df.columns:
        df["nombre"] = df["nombre"].fillna("")
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df.reset_index(drop=True)


def guardar_seccion(mes, seccion, df):
    """Reemplaza todas las filas de (mes, seccion) con las del DataFrame."""
    cols = SECCIONES[seccion]
    with conectar() as con:
        con.execute("DELETE FROM items WHERE mes = ? AND seccion = ?",
                    (mes, seccion))
        for orden, (_, fila) in enumerate(df.iterrows()):
            nombre = str(fila.get("nombre", "") or "").strip()
            total = num(fila.get("total"))
            presupuesto = num(fila.get("presupuesto"))
            real = num(fila.get("real"))
            if not nombre and total == 0 and presupuesto == 0 and real == 0:
                continue  # ignorar filas vacías
            con.execute(
                "INSERT INTO items (mes, seccion, nombre, fecha, total, "
                "presupuesto, real, pagado, orden) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    mes, seccion, nombre,
                    _fecha_a_texto(fila.get("fecha")) if "fecha" in cols else "",
                    total if "total" in cols else 0,
                    presupuesto, real,
                    int(bool(fila.get("pagado", 0))) if "pagado" in cols else 0,
                    orden,
                ),
            )
        con.commit()


def crear_mes(mes, copiar_de=None):
    """Crea un mes nuevo. Si 'copiar_de' se indica, copia TODO ese mes tal cual
    (presupuesto, real, fechas) para que el usuario lo ajuste. Si no, precarga
    los gastos mensuales fijos."""
    if copiar_de:
        for seccion in SECCIONES:
            df = cargar_seccion(copiar_de, seccion)
            if not df.empty:
                guardar_seccion(mes, seccion, df.copy())
    else:
        df = pd.DataFrame([
            {"nombre": g["nombre"], "presupuesto": g["presupuesto"], "real": 0.0}
            for g in GASTOS_PREDEFINIDOS
        ])
        guardar_seccion(mes, "gasto", df)


def eliminar_mes(mes):
    """Borra por completo un mes y todos sus registros."""
    with conectar() as con:
        con.execute("DELETE FROM items WHERE mes = ?", (mes,))
        con.commit()


# --------------------------------------------------------------------------- #
# Préstamos (tabla global)
# --------------------------------------------------------------------------- #
def cargar_prestamos():
    """DataFrame con todos los préstamos (tabla global, no por mes)."""
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT persona, nombre, fecha, total, devuelto FROM prestamos "
            "ORDER BY orden, id", con,
        )
    if df.empty:
        df = pd.DataFrame(columns=PRESTAMOS_COLS)
    df["persona"] = df["persona"].fillna("")
    df["nombre"] = df["nombre"].fillna("")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for c in ("total", "devuelto"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df.reset_index(drop=True)


def guardar_prestamos(df):
    """Reemplaza toda la tabla global de préstamos con el DataFrame."""
    with conectar() as con:
        con.execute("DELETE FROM prestamos")
        for orden, (_, fila) in enumerate(df.iterrows()):
            persona = str(fila.get("persona", "") or "").strip()
            nombre = str(fila.get("nombre", "") or "").strip()
            total = num(fila.get("total"))
            devuelto = num(fila.get("devuelto"))
            if not persona and not nombre and total == 0 and devuelto == 0:
                continue
            con.execute(
                "INSERT INTO prestamos (persona, nombre, fecha, total, devuelto, "
                "orden) VALUES (?, ?, ?, ?, ?, ?)",
                (persona, nombre, _fecha_a_texto(fila.get("fecha")),
                 total, devuelto, orden),
            )
        con.commit()


# --------------------------------------------------------------------------- #
# Tarjeta de crédito (tabla global)
# --------------------------------------------------------------------------- #
def cargar_tarjeta():
    """DataFrame con todas las compras de tarjeta (tabla global aislada)."""
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT concepto, persona, fecha, total, cuotas, pagado "
            "FROM tarjeta ORDER BY orden, id", con,
        )
    if df.empty:
        df = pd.DataFrame(columns=TARJETA_COLS)
    df["concepto"] = df["concepto"].fillna("")
    df["persona"] = df["persona"].fillna("")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for c in ("total", "pagado"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["cuotas"] = pd.to_numeric(
        df["cuotas"], errors="coerce").fillna(1).astype(int)
    return df.reset_index(drop=True)


def guardar_tarjeta(df):
    """Reemplaza toda la tabla global de tarjeta con el DataFrame."""
    with conectar() as con:
        con.execute("DELETE FROM tarjeta")
        for orden, (_, fila) in enumerate(df.iterrows()):
            concepto = str(fila.get("concepto", "") or "").strip()
            persona = str(fila.get("persona", "") or "").strip()
            total = num(fila.get("total"))
            pagado = num(fila.get("pagado"))
            try:
                cuotas = int(fila.get("cuotas", 1) or 1)
            except (ValueError, TypeError):
                cuotas = 1
            if not concepto and not persona and total == 0 and pagado == 0:
                continue
            con.execute(
                "INSERT INTO tarjeta (concepto, persona, fecha, total, cuotas, "
                "pagado, orden) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (concepto, persona, _fecha_a_texto(fila.get("fecha")),
                 total, cuotas, pagado, orden),
            )
        con.commit()


# --------------------------------------------------------------------------- #
# Metas de ahorro (tabla global)
# --------------------------------------------------------------------------- #
def cargar_metas():
    """DataFrame con las metas de ahorro (tabla global)."""
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT nombre, objetivo, ahorrado FROM metas ORDER BY orden, id",
            con,
        )
    if df.empty:
        df = pd.DataFrame(columns=METAS_COLS)
    df["nombre"] = df["nombre"].fillna("")
    for c in ("objetivo", "ahorrado"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df.reset_index(drop=True)


def guardar_metas(df):
    """Reemplaza toda la tabla global de metas con el DataFrame."""
    with conectar() as con:
        con.execute("DELETE FROM metas")
        for orden, (_, fila) in enumerate(df.iterrows()):
            nombre = str(fila.get("nombre", "") or "").strip()
            objetivo = num(fila.get("objetivo"))
            ahorrado = num(fila.get("ahorrado"))
            if not nombre and objetivo == 0 and ahorrado == 0:
                continue
            con.execute(
                "INSERT INTO metas (nombre, objetivo, ahorrado, orden) "
                "VALUES (?, ?, ?, ?)",
                (nombre, objetivo, ahorrado, orden),
            )
        con.commit()
