#!/bin/bash
# Doble clic para abrir el Gestor de Finanzas en el navegador.
cd "$(dirname "$0")"
echo "Iniciando Gestor de Finanzas..."
echo "Se abrira en tu navegador. Para cerrar, cierra esta ventana."
.venv/bin/streamlit run app_finanzas.py
