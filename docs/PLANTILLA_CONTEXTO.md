# Plantilla de Contexto para Proyectos

> Copia esta plantilla para documentar cualquier proyecto nuevo

---

## 📋 GUÍA RÁPIDA DE USO

**Cuándo actualizar este archivo:**
- ✅ Después de tomar decisiones técnicas importantes
- ✅ Al completar una funcionalidad mayor
- ✅ Cuando cambies la arquitectura
- ✅ Al encontrar problemas o limitaciones
- ✅ Antes de pausar el proyecto por tiempo prolongado

**Cómo usarlo en chats futuros:**
- Menciona: "Revisa CONTEXTO_PROYECTO.md para entender el estado actual"
- El archivo debe ser autoexplicativo sin necesidad de contexto adicional

---

## 🎯 Objetivo del Proyecto
[Una o dos frases que expliquen QUÉ hace la aplicación y PARA QUÉ]

**Ejemplo:**
> Aplicación local para registrar gastos e ingresos personales con interfaz gráfica y almacenamiento en base de datos.

---

## 🏗️ Arquitectura

### Stack Tecnológico
- **Frontend/UI**: [Tecnología elegida]
- **Backend/Lógica**: [Tecnología elegida]
- **Base de Datos**: [Tecnología elegida]
- **Lenguaje**: [Lenguaje principal]

### ¿Por qué estas tecnologías?
- [Tecnología 1]: [Razón específica]
- [Tecnología 2]: [Razón específica]

---

## 📁 Estructura de Archivos

```
/proyecto/
├── archivo1.py          # Descripción breve
├── archivo2.py          # Descripción breve
├── carpeta/
│   └── modulo.py        # Descripción breve
└── README.md
```

---

## 👥 División de Responsabilidades

### ✅ Completado: [Rol/Área]
**Archivos**: `archivo1.py`, `archivo2.py`

**Funcionalidades:**
- [x] Funcionalidad 1
- [x] Funcionalidad 2

**Métodos/APIs disponibles:**
```python
metodo1()  # Descripción
metodo2()  # Descripción
```

### 🔨 Pendiente: [Rol/Área]
**Archivos de trabajo**: `archivo_pendiente.py`

**Tareas:**
- [ ] Tarea 1
- [ ] Tarea 2
- [ ] Tarea 3

---

## 📊 Estructura de Datos

### Base de Datos
```sql
-- Tabla principal
CREATE TABLE nombre_tabla (
    id INTEGER PRIMARY KEY,
    campo1 TEXT,
    campo2 REAL
);
```

### Formatos de Datos
```python
# Formato 1: Descripción
{
    'campo1': 'valor',
    'campo2': 123
}

# Formato 2: Descripción
(id, campo1, campo2)
```

---

## 📦 Dependencias

### Incluidas con Python
- `libreria1` - Para qué se usa
- `libreria2` - Para qué se usa

### Requieren instalación
```bash
pip install libreria3
pip install libreria4
```

---

## 🎯 Estado Actual

### Completado
- [x] Funcionalidad principal 1
- [x] Funcionalidad principal 2

### En Progreso
- [ ] Funcionalidad en desarrollo

### Pendiente
- [ ] Funcionalidad futura 1
- [ ] Funcionalidad futura 2

---

## 🚀 Próximos Pasos

**Prioridad Alta:**
1. [Tarea más importante]
2. [Segunda tarea importante]

**Prioridad Media:**
3. [Tarea opcional pero útil]

**Prioridad Baja:**
4. [Mejora futura]

---

## ⚠️ Problemas Conocidos

- **Problema 1**: Descripción breve
  - Workaround temporal: [Solución]
  
- **Limitación 1**: Descripción
  - Razón: [Por qué existe]

---

## 💡 Convenciones del Proyecto

### Nombres de Archivos
- `snake_case.py` para módulos
- `PascalCase` para clases

### Nombres de Funciones
- `verbo_sustantivo()` - Ejemplo: `obtener_datos()`

### Comentarios
- Mínimos, código autoexplicativo
- Solo para lógica compleja

---

## 📝 Notas Importantes

- [Nota relevante 1]
- [Nota relevante 2]
- [Decisión importante que no debe olvidarse]

---

## 📅 Historial de Cambios

**[Fecha]** - [Descripción del cambio mayor]
- Detalle 1
- Detalle 2

**[Fecha]** - [Otro cambio importante]
- Detalle

---

**Última actualización**: [Fecha]
**Estado**: [En desarrollo / Pausado / Completado]
**Responsable actual**: [Quién está trabajando en qué]
