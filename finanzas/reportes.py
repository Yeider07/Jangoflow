"""Cálculos y agregaciones sobre los datos (capa de dominio/reportes).

No escribe nada: solo lee de la base y calcula totales, patrimonio, históricos
y los datos para las gráficas.
"""

import pandas as pd

from finanzas.categorias import categorizar
from finanzas.db import conectar, listar_meses
from finanzas.formato import num


# --------------------------------------------------------------------------- #
# Resumen de un mes
# --------------------------------------------------------------------------- #
def resumen_mes(mes):
    """Totales del mes para el Dashboard y el cálculo de disponible."""
    def total(seccion, col):
        with conectar() as con:
            r = con.execute(
                f"SELECT COALESCE(SUM({col}), 0) AS t FROM items "
                "WHERE mes = ? AND seccion = ?", (mes, seccion),
            ).fetchone()
        return float(r["t"])

    def reservado(seccion):
        """Suma del mayor entre presupuesto y real de cada fila (reserva el
        presupuesto completo, sin contar doble si ya se pagó)."""
        with conectar() as con:
            r = con.execute(
                "SELECT COALESCE(SUM(MAX(presupuesto, real)), 0) AS t "
                "FROM items WHERE mes = ? AND seccion = ?", (mes, seccion),
            ).fetchone()
        return float(r["t"])

    ingresos_real = total("ingreso", "real")
    ingresos_esp = total("ingreso", "presupuesto")
    compras_real = total("compra_libre", "real")          # gasto diario
    gastos_mens_real = total("gasto", "real")
    gastos_mens_esp = total("gasto", "presupuesto")
    gastos_mens_reservado = reservado("gasto")
    gastos_real = compras_real + gastos_mens_real
    gastos_esp = gastos_mens_esp
    ahorros_real = total("ahorro", "real")
    ahorros_esp = total("ahorro", "presupuesto")
    invertido_real = total("invertido", "real")
    deudas_real = total("deuda", "real")                  # pagado este mes
    deudas_esp = total("deuda", "presupuesto")            # cuota mensual
    deudas_reservado = reservado("deuda")

    # Disponible: reserva el presupuesto de gastos y la cuota de deudas; compras
    # libres, ahorros e invertido descuentan solo lo realmente movido.
    disponible = (ingresos_real - compras_real - gastos_mens_reservado
                  - ahorros_real - invertido_real - deudas_reservado)

    return {
        "ingresos_real": ingresos_real,
        "ingresos_esp": ingresos_esp,
        "compras_real": compras_real,
        "gastos_mens_real": gastos_mens_real,
        "gastos_mens_esp": gastos_mens_esp,
        "gastos_mens_reservado": gastos_mens_reservado,
        "gastos_real": gastos_real,
        "gastos_esp": gastos_esp,
        "ahorros_real": ahorros_real,
        "ahorros_esp": ahorros_esp,
        "invertido_real": invertido_real,
        "deudas_real": deudas_real,
        "deudas_esp": deudas_esp,
        "deudas_reservado": deudas_reservado,
        "disponible": disponible,
    }


def resumen_historico(meses=None):
    """DataFrame con el resumen por mes. Si 'meses' es una lista, solo esos."""
    filas = []
    todos = sorted(listar_meses())
    if meses is not None:
        todos = [m for m in todos if m in set(meses)]
    for mes in todos:
        r = resumen_mes(mes)
        r["mes"] = mes
        filas.append(r)
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Préstamos (global)
# --------------------------------------------------------------------------- #
def prestamos_por_nombre():
    """Por cada préstamo de la tabla global: (nombre, total, devuelto)."""
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, total, devuelto FROM prestamos "
            "WHERE total <> 0 OR devuelto <> 0 ORDER BY total DESC"
        ).fetchall()
    return [
        (f["nombre"], num(f["total"]), num(f["devuelto"]))
        for f in filas if f["nombre"]
    ]


def prestado_pendiente_total():
    """Suma de lo pendiente por cobrar de todos los préstamos."""
    return sum(max(tot - dev, 0) for _, tot, dev in prestamos_por_nombre())


# --------------------------------------------------------------------------- #
# Patrimonio acumulado
# --------------------------------------------------------------------------- #
def totales_generales(meses=None):
    """Suma acumulada de los meses indicados (o todos) + patrimonio.
    El prestado es global y no se filtra por mes."""
    df = resumen_historico(meses)
    if df.empty:
        return {"ingresos": 0.0, "gastos": 0.0, "ahorros": 0.0,
                "ahorro_liquido": 0.0, "invertido": 0.0,
                "prestado_pendiente": 0.0, "patrimonio": 0.0,
                "deudas": 0.0, "disponible": 0.0, "meses": 0}
    ahorros = float(df["ahorros_real"].sum())   # incluye lo prestado
    invertido = float(df["invertido_real"].sum())
    prestado_pend = prestado_pendiente_total()
    return {
        "ingresos": float(df["ingresos_real"].sum()),
        "gastos": float(df["gastos_real"].sum()),
        "ahorros": ahorros,
        "ahorro_liquido": ahorros - prestado_pend,
        "invertido": invertido,
        "prestado_pendiente": prestado_pend,
        "patrimonio": ahorros + invertido,   # el prestado ya está en ahorros
        "deudas": float(df["deudas_real"].sum()),
        "disponible": float(df["disponible"].sum()),
        "meses": int(len(df)),
    }


def invertido_acumulado(meses=None):
    """DataFrame por mes con lo invertido ese mes y el acumulado."""
    df = resumen_historico(meses)
    if df.empty or "invertido_real" not in df:
        return pd.DataFrame(columns=["mes", "invertido_mes", "acumulado"])
    out = df[["mes", "invertido_real"]].copy()
    out = out.rename(columns={"invertido_real": "invertido_mes"})
    out["acumulado"] = out["invertido_mes"].cumsum()
    return out


def ahorros_acumulados(meses=None):
    """DataFrame por mes con el ahorro de ese mes y el acumulado."""
    df = resumen_historico(meses)
    if df.empty:
        return pd.DataFrame(columns=["mes", "ahorro_mes", "acumulado"])
    out = df[["mes", "ahorros_real"]].copy()
    out = out.rename(columns={"ahorros_real": "ahorro_mes"})
    out["acumulado"] = out["ahorro_mes"].cumsum()
    return out


# --------------------------------------------------------------------------- #
# Agregaciones por nombre / categoría
# --------------------------------------------------------------------------- #
def _filtro_meses(meses):
    """Devuelve (clausula_sql, params) para filtrar por una lista de meses."""
    if not meses:
        return "", []
    ph = ",".join("?" * len(meses))
    return f" AND mes IN ({ph})", list(meses)


def ahorros_por_nombre(meses=None):
    """Total acumulado de cada ahorro (por nombre) en los meses indicados."""
    clausula, params = _filtro_meses(meses)
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, SUM(real) AS total FROM items "
            f"WHERE seccion = 'ahorro'{clausula} GROUP BY nombre "
            "HAVING total <> 0 ORDER BY total DESC", params,
        ).fetchall()
    return {f["nombre"]: float(f["total"]) for f in filas if f["nombre"]}


def ahorros_detalle_por_mes(meses=None):
    """Pivot mes x tipo de ahorro (para barras apiladas)."""
    clausula, params = _filtro_meses(meses)
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT mes, nombre, SUM(real) AS total FROM items "
            f"WHERE seccion = 'ahorro' AND real <> 0{clausula} "
            "GROUP BY mes, nombre", con, params=params,
        )
    if df.empty:
        return pd.DataFrame()
    return df.pivot_table(index="mes", columns="nombre", values="total",
                          aggfunc="sum", fill_value=0).sort_index()


def deudas_por_nombre(meses=None):
    """Por cada deuda: total (sin duplicar entre meses, se toma el mayor) y lo
    pagado acumulado. Lista de tuplas (nombre, total, pagado)."""
    clausula, params = _filtro_meses(meses)
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, MAX(total) AS total, SUM(real) AS pagado "
            f"FROM items WHERE seccion = 'deuda'{clausula} GROUP BY nombre "
            "HAVING total <> 0 OR pagado <> 0 ORDER BY total DESC", params,
        ).fetchall()
    return [
        (f["nombre"], num(f["total"]), num(f["pagado"]))
        for f in filas if f["nombre"]
    ]


def gastos_por_categoria(mes):
    """{nombre: real} de los gastos mensuales (para la gráfica de pastel)."""
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, SUM(real) AS total FROM items "
            "WHERE mes = ? AND seccion = 'gasto' AND real > 0 "
            "GROUP BY nombre ORDER BY total DESC", (mes,),
        ).fetchall()
    return {f["nombre"]: float(f["total"]) for f in filas if f["nombre"]}


def gastos_categorizados(mes, secciones=("compra_libre",)):
    """Gasto del mes agrupado por categoría AUTOMÁTICA (según la descripción).

    Por defecto solo las compras libres (gasto diario), que son las que tienen
    descripción libre y se benefician de categorizarse. Devuelve
    {categoria: total} ordenado de mayor a menor."""
    ph = ",".join("?" * len(secciones))
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, SUM(real) AS total FROM items "
            f"WHERE mes = ? AND seccion IN ({ph}) AND real > 0 "
            "GROUP BY nombre", (mes, *secciones),
        ).fetchall()
    acum = {}
    for f in filas:
        cat = categorizar(f["nombre"])
        acum[cat] = acum.get(cat, 0.0) + float(f["total"])
    return dict(sorted(acum.items(), key=lambda kv: kv[1], reverse=True))


def gastos_libres_categorizados(meses=None):
    """Compras libres agrupadas por categoría automática en TODO el periodo.

    Como gastos_categorizados pero sobre varios meses (o todos): sirve para ver
    qué categorías usas más a lo largo del tiempo. {categoria: total} de mayor a
    menor."""
    clausula, params = _filtro_meses(meses)
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, SUM(real) AS total FROM items "
            f"WHERE seccion = 'compra_libre' AND real > 0{clausula} "
            "GROUP BY nombre", params,
        ).fetchall()
    acum = {}
    for f in filas:
        cat = categorizar(f["nombre"])
        acum[cat] = acum.get(cat, 0.0) + float(f["total"])
    return dict(sorted(acum.items(), key=lambda kv: kv[1], reverse=True))


def gasto_detalle_categoria(mes, categoria, secciones=("compra_libre",)):
    """Descripciones (sub-categorías reales) que componen una categoría en el
    mes. Devuelve {descripcion: total} ordenado de mayor a menor."""
    ph = ",".join("?" * len(secciones))
    with conectar() as con:
        filas = con.execute(
            "SELECT nombre, SUM(real) AS total FROM items "
            f"WHERE mes = ? AND seccion IN ({ph}) AND real > 0 "
            "GROUP BY nombre", (mes, *secciones),
        ).fetchall()
    detalle = {f["nombre"]: float(f["total"]) for f in filas
               if f["nombre"] and categorizar(f["nombre"]) == categoria}
    return dict(sorted(detalle.items(), key=lambda kv: kv[1], reverse=True))


def gasto_diario(mes):
    """DataFrame fecha -> total de las compras libres del mes (gasto del día a
    día), ordenado por fecha. Vacío si no hay compras con fecha."""
    with conectar() as con:
        df = pd.read_sql_query(
            "SELECT fecha, SUM(real) AS total FROM items "
            "WHERE mes = ? AND seccion = 'compra_libre' AND real > 0 "
            "AND fecha IS NOT NULL AND fecha <> '' "
            "GROUP BY fecha ORDER BY fecha", con, params=(mes,),
        )
    if df.empty:
        return pd.DataFrame(columns=["fecha", "total"])
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df.dropna(subset=["fecha"]).reset_index(drop=True)
