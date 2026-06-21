# 💰 Gestor de Finanzas Personales

Aplicación web local (Streamlit) para llevar tus finanzas **mes a mes**, al estilo
de un dashboard de Excel: ingresos, gastos, ahorros, inversiones, préstamos y
deudas, con patrimonio acumulado, simulador de crédito hipotecario y seguimiento
de tarjeta de crédito.

Todo se guarda **localmente** en `finanzas.db` (SQLite). No necesita internet ni
servidor externo.

---

## 🚀 Cómo ejecutarla

```bash
cd /Users/yeider/Documentos/Aplicacion_Finanzas
.venv/bin/streamlit run app_finanzas.py
```

Se abre en el navegador en **http://localhost:8501**.

> El entorno usa **Python 3.12** (en `.venv`). Dependencias en `requirements.txt`
> (`streamlit`, `plotly`, `pandas`). Para reinstalar:
> `.venv/bin/pip install -r requirements.txt`.

### 📱 Verla en el celular (misma red Wi-Fi)
Con la app corriendo en el Mac, abre en el celular la **Network URL** que muestra
Streamlit al arrancar (ej. `http://192.168.1.X:8501`). El Mac debe estar encendido.

---

## 🧭 Secciones (selector "📂 Sección" en la barra lateral)

La app tiene tres áreas independientes:

### 💰 Finanzas (pestañas)
| Pestaña | Para qué sirve |
|---|---|
| 🌎 **General** | Patrimonio acumulado (ahorro total/líquido, invertido, por cobrar, patrimonio) y gráficas. Incluye un **selector de meses** para filtrar y proyectar. |
| 📊 **Dashboard** | Resumen del **mes activo**: tarjetas, Presupuesto vs Real, distribución de gastos. |
| ✏️ **Registrar / Editar** | Tablas editables por mes: Ingresos, Compras libres, Gastos, Ahorros, Invertido, Deudas. |
| 📈 **Histórico** | Evolución mes a mes (ingresos, gastos, disponible). |

### 💳 Tarjeta de crédito
Seguimiento **aislado** (no afecta finanzas) de compras y diferidos de la tarjeta,
útil cuando prestas la tarjeta. Tabla global con Total / Pagado / Pendiente.

### 🏠 Crédito hipotecario
**Simulador**: calcula cuota, tabla de amortización e intereses. Permite agregar
abonos a capital (mensual, arriendo temporal, prima y cesantías anuales) y muestra
cuánto **tiempo e intereses ahorras**. No guarda datos (es solo simulación).

---

## 🤝 Prestado (pestaña propia, global)
El dinero que prestas **no va por mes** — vive en una lista global hasta que te
paguen. Registras Total prestado y Devuelto; lo pendiente por cobrar se **descuenta
del ahorro líquido** en el General.

---

## 📅 Manejo de meses (barra lateral, en Finanzas)

- **Crear nuevo mes**: eliges año y mes. Opción de **copiar el presupuesto del mes
  anterior** (trae lo planeado y deja el Real en $0).
- **Mes activo**: selector para ver/editar cualquier mes.
- **Eliminar mes**: borra un mes y sus registros (con confirmación).

---

## 🗂️ Estructura del proyecto

El código usa una **arquitectura modular por capas** (paquete `finanzas/`):

```
Aplicacion_Finanzas/
├── app_finanzas.py              # Punto de entrada (solo configura y enruta)
├── finanzas/                    # Paquete principal
│   ├── config.py                # Constantes y rutas
│   ├── formato.py               # Utilidades (pesos, fechas, num)
│   ├── db.py                    # Acceso a SQLite (conexión, migraciones, CRUD)
│   ├── reportes.py              # Cálculos y agregaciones
│   ├── hipoteca.py              # Lógica del simulador (sin Streamlit)
│   └── vistas/                  # Una vista por archivo (Streamlit)
│       ├── sidebar.py · dashboard.py · general.py · registrar.py
│       ├── historico.py · metas.py · prestado.py · tarjeta.py
│       └── hipotecario.py · componentes.py
├── tests/                       # Tests de la lógica pura (pytest)
├── docs/                        # Documentación del proyecto
│   ├── CONTEXTO_PROYECTO.md     # Estado y decisiones del proyecto
│   └── PLANTILLA_CONTEXTO.md    # Plantilla genérica de contexto (reutilizable)
├── .streamlit/config.toml       # Tema y configuración de Streamlit
├── Iniciar Finanzas.command     # Arranque por doble clic (macOS)
├── finanzas.db                  # Base de datos local (se crea/migra sola)
├── backups/                     # Respaldos automáticos diarios (rotados)
├── requirements.txt             # Dependencias de la app
├── requirements-dev.txt         # Dependencias de desarrollo (pytest)
├── README.md                    # Esta guía
└── .venv/                       # Entorno virtual (Python 3.12)
```

> Para tocar la lógica de un cálculo, ve a `finanzas/reportes.py` o `db.py`.
> Para cambiar cómo se ve una pantalla, ve a su archivo en `finanzas/vistas/`.

---

## 💾 Tus datos están seguros

- Los datos viven en `finanzas.db`, **separados del código**.
- Reiniciar el servidor, refrescar el navegador o cambiar el código **no borra** nada.
- Solo borran datos: "Eliminar mes", eliminar filas, o borrar `finanzas.db`.

> **Respaldo:** copia el archivo `finanzas.db` a otra carpeta cuando quieras una
> copia de seguridad (ya existe una: `finanzas_backup_2026-06-08.db`).
