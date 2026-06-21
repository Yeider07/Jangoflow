# Contexto del Proyecto: Gestor de Finanzas Personales

> Documento de estado. Léelo para entender qué hace la app, cómo está armada y
> por qué se tomaron las decisiones clave.

**Última actualización**: 2026-06-14
**Estado**: Funcional, en uso. App web local con patrimonio, préstamos,
tarjeta de crédito y simulador hipotecario. Código refactorizado a una
**arquitectura modular por capas** (paquete `finanzas/`).

---

## 📌 Objetivo

Aplicación **web local** para llevar las finanzas personales **mes a mes**, al
estilo de un dashboard de Excel: registrar ingresos, gastos, ahorros, inversiones,
préstamos y deudas; ver patrimonio acumulado, proyectar ahorro y simular un crédito
hipotecario.

---

## 🏗️ Stack y arquitectura

- **UI**: Streamlit (tablas editables tipo Excel + pestañas + selector de sección)
- **Gráficas**: Plotly
- **Datos**: SQLite (archivo local `finanzas.db`), manipulado con pandas
- **Lenguaje**: **Python 3.12** (entorno en `.venv`). *Se migró desde 3.14 porque
  varias librerías de la nube no soportaban 3.14.*

### Arquitectura por capas (paquete `finanzas/`)

Dependencias en una sola dirección: config → formato → db → reportes → vistas.

```
app_finanzas.py           -> Punto de entrada DELGADO: configura, init_db y enruta
finanzas/
├── config.py             -> Constantes y rutas (sin dependencias)
├── formato.py            -> Utilidades: pesos, etiqueta_mes, num, fechas
├── db.py                 -> Acceso a SQLite: conexión, migraciones, CRUD
├── reportes.py           -> Cálculos y agregaciones (lee, no escribe)
├── hipoteca.py           -> Lógica pura del simulador (sin Streamlit, testeable)
└── vistas/               -> Capa de presentación (una vista por archivo)
    ├── sidebar.py        -> Selector de sección + gestión de meses
    ├── dashboard.py      -> Resumen del mes activo
    ├── general.py        -> Patrimonio acumulado (filtrable por meses)
    ├── registrar.py      -> Tablas editables por mes (sub-pestañas)
    ├── historico.py      -> Evolución mes a mes
    ├── prestado.py       -> Préstamos (global)
    ├── tarjeta.py        -> Tarjeta de crédito (global, aislada)
    ├── hipotecario.py    -> Simulador de crédito
    └── componentes.py    -> Componentes UI reutilizables (input_pesos)
finanzas.db               -> Base de datos local (se crea/migra sola al iniciar)
```

Ejecutar: `.venv/bin/streamlit run app_finanzas.py` → http://localhost:8501
(o doble clic en **"Iniciar Finanzas.command"**).

> ⚠️ Streamlit recarga solo el archivo principal al editarlo. Si se cambia un
> módulo de `finanzas/`, hay que **reiniciar el servidor**.

> 🧪 Para probar sin abrir el navegador: el framework `streamlit.testing.v1`
> (`AppTest.from_file("app_finanzas.py").run()`) ejecuta la app y reporta
> excepciones; útil tras cambios grandes.

---

## 🧱 Tres secciones (selector "📂 Sección" en la barra lateral)

1. **💰 Finanzas** — pestañas: General, Dashboard, Registrar/Editar, Histórico.
2. **💳 Tarjeta de crédito** — seguimiento aislado (tabla global `tarjeta`); NO
   afecta los cálculos de finanzas.
3. **🏠 Crédito hipotecario** — simulador puro (no persiste datos).

Las vistas de Tarjeta e Hipotecario usan `st.stop()` para aislarse de Finanzas.

---

## 🗃️ Modelo de datos

### Tabla `items` (registros por mes)
| Columna | Uso |
|---|---|
| `mes` | 'YYYY-MM' |
| `seccion` | ingreso · compra_libre · gasto · ahorro · invertido · deuda |
| `nombre`, `fecha` | concepto y fecha ('YYYY-MM-DD'; en la UI es calendario) |
| `total` | solo deudas: total de la deuda |
| `presupuesto` | planeado (gastos, deudas=cuota mensual) |
| `real` | lo realmente movido |
| `pagado` | solo compras libres: checkbox |
| `orden` | orden de filas |

### Tabla `prestamos` (GLOBAL, no por mes)
Dinero que prestaste, vive hasta que te paguen. `nombre`, `fecha`, `total`
(prestado), `devuelto`.

### Tabla `tarjeta` (GLOBAL, aislada)
Seguimiento de tarjeta de crédito. `concepto`, `persona`, `fecha`, `total`,
`cuotas`, `pagado`.

### Significado de cada sección de `items`
| Sección | Columnas que edita el usuario | Notas |
|---|---|---|
| **ingreso** | nombre, fecha, real (= "Monto") | Ingresos fijos, solo monto. |
| **compra_libre** | pagado, nombre, fecha, real (= "Gasto") | Gasto diario, sin presupuesto. |
| **gasto** | nombre, presupuesto, real | Presupuesto mensual de gastos. |
| **ahorro** | nombre, real (= "Ahorrado") | Aporte de ahorro del mes (líquido). Se suma. |
| **invertido** | nombre, real (= "Invertido") | Aporte de inversión del mes (no líquido). Se suma. |
| **deuda** | nombre, total, presupuesto (= "Cuota mes"), real (= "Pagado") | Deuda a cuotas. |

---

## 🧮 Cálculos clave

**Disponible para gastar (por mes):**
```
Disponible = Ingresos − Compras libres − Gastos mensuales (reservados)
           − Ahorros − Invertido − Cuota de deudas (reservada)
```
"Reservado" = `max(presupuesto, real)` por fila → reserva el presupuesto completo
aunque no se haya pagado, sin contar doble si ya se pagó.

**Patrimonio (acumulado en General, filtrable por meses):**
```
Ahorro total      = Σ ahorros (INCLUYE lo prestado)
Invertido         = Σ invertido
Prestado pendiente = Σ (total − devuelto) de la tabla prestamos  (global)
Ahorro líquido    = Ahorro total − Prestado pendiente
Patrimonio total  = Ahorro total + Invertido
```
El dinero prestado está dentro del ahorro total (salió de ahí), por eso se
**descuenta** para el líquido y NO se suma aparte en el patrimonio.

**General filtrable:** un `multiselect` de meses filtra todas las tarjetas y
gráficas (excepto Prestado, que es global). Sirve para proyectar el ahorro.

**Simulador hipotecario:** cuota = sistema francés con tasa mensual
`(1+EA)^(1/12)−1`. Soporta abonos a capital (mensual, arriendo temporal, prima y
cesantías anuales) y calcula el ahorro en tiempo e intereses. Ingresos requeridos
≈ cuota ÷ 0.4.

---

## 🔁 Migraciones (PRAGMA user_version)

La app migra sola la BD al iniciar:
- **v1**: deudas → `total` = deuda completa, `presupuesto` = cuota mensual.
- **v2**: mover "Prestado" e "Invertido" desde Ahorros a sus secciones propias.
- **v3**: mover préstamos de `items` (por mes) a la tabla global `prestamos`.

---

## 🎨 Decisiones de diseño (el "por qué")

- **Streamlit (no Tkinter)**: dashboards y tablas editables con poco código, en el
  navegador. (La versión Tkinter original se eliminó.)
- **Ahorros/Invertido como aporte mensual** (no saldo): se registra lo del mes y se
  suma en General → control granular.
- **Préstamos y Tarjeta globales**: no pertenecen a un mes; arrastrarlos cada mes
  era mala práctica.
- **Reservar presupuesto de gastos/deudas**: el disponible refleja compromisos
  planeados, no solo lo pagado.
- **Python 3.12**: máxima compatibilidad de librerías (3.14 daba problemas).

---

## 🐛 Notas técnicas / problemas resueltos

- **Bug de `st.data_editor` al cambiar de mes**: el editor reaplicaba cambios
  viejos al mes equivocado y sobrescribía datos. Solución: limpiar el estado del
  editor (`st.session_state`) al cambiar de mes y después de guardar.
- **Celdas numéricas vacías (NaN)**: la función `num()` en `finanzas/formato.py`
  convierte vacío/None/NaN a 0 de forma segura en todas las lecturas y guardados.

---

## 🚧 Mejoras pendientes / ideas

- **Respaldo automático** de `finanzas.db` al iniciar (recomendado; ya hubo una
  pérdida de datos por el bug del editor). Hay un respaldo manual:
  `finanzas_backup_2026-06-08.db`.
- **Subir a la nube** + contraseña (evaluado: Streamlit Cloud + Turso gratis, o
  host pago ~$5/mes; pospuesto, se sigue local).
- **Pronóstico de ahorro + metas** (promedio mensual, proyección, progreso).
- **Exportar a Excel/CSV.**
- Tarjeta: cuota mensual de diferidos. Deudas: línea de tiempo de pago total.

---

## 🗂️ Otros archivos del proyecto

- `.streamlit/config.toml` — tema (oscuro + azul), menú minimal, headless/puerto.
- `Iniciar Finanzas.command` — arranque por doble clic (macOS).
- `requirements.txt` — dependencias de la app (streamlit, plotly, pandas).
- `requirements-dev.txt` — dependencias de desarrollo (pytest).
- `tests/` — tests de la lógica pura (`hipoteca`, `formato`); correr con `pytest`.
- `backups/` — respaldos automáticos diarios de la base (rotados, ver `db.respaldar_db`).
- `docs/PLANTILLA_CONTEXTO.md` — plantilla genérica reutilizable (no es de esta app).
