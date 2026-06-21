"""Componentes de UI reutilizables."""

import re

import streamlit as st

from finanzas.formato import pesos


def _formatear_pesos_input(key):
    """Callback: reformatea el texto de un input a formato pesos ($1.234.567)."""
    digitos = re.sub(r"[^\d]", "", st.session_state.get(key, "") or "")
    st.session_state[key] = pesos(int(digitos)) if digitos else "$0"


def input_pesos(label, key, default, help=None):
    """Campo de texto que se muestra y edita en formato pesos. Devuelve el
    valor entero."""
    if key not in st.session_state:
        st.session_state[key] = pesos(int(default))
    st.text_input(label, key=key, on_change=_formatear_pesos_input,
                  args=(key,), help=help)
    digitos = re.sub(r"[^\d]", "", st.session_state[key] or "")
    return int(digitos) if digitos else 0
