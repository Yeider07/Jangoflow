"""Gestor de Finanzas Personales — paquete principal.

Arquitectura por capas:
    config   -> constantes y rutas (sin dependencias)
    formato  -> utilidades de formato y conversión (sin dependencias de datos)
    db       -> acceso a SQLite (conexión, migraciones, CRUD)
    reportes -> cálculos y agregaciones sobre los datos
    hipoteca -> lógica del simulador de crédito
    vistas/  -> capa de presentación (Streamlit), una vista por archivo
"""
