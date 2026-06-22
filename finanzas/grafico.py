"""Tema visual minimalista para los gráficos de Plotly.

Centraliza el estilo para que todas las vistas se vean iguales y sobrias:
fondo transparente (se integra al tema oscuro), sin bordes ni cajas, grilla
casi invisible, tipografía ligera y paleta apagada. Las vistas solo construyen
los datos y llaman a `estilizar(fig)`.
"""

# Paleta apagada (desaturada) para series sin categoría fija.
PALETA = ["#7C9EB2", "#A8C686", "#E0A458", "#C97B84", "#9A8FB0",
          "#7BB0A8", "#C2B280", "#B0917D"]

COLOR_TEXTO = "#C9CDD4"          # texto tenue
COLOR_TENUE = "#8A8F98"          # ejes/secundario
COLOR_GRID = "rgba(255,255,255,0.06)"  # grilla casi invisible
FUENTE = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def estilizar(fig, alto=320, grid_y=True, grid_x=False, leyenda=True):
    """Aplica el estilo minimalista a una figura y la devuelve."""
    fig.update_layout(
        height=alto,
        margin=dict(t=28, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, color=COLOR_TEXTO, size=13),
        hoverlabel=dict(bgcolor="#1A1F2B", bordercolor="rgba(0,0,0,0)",
                        font=dict(family=FUENTE, color=COLOR_TEXTO, size=12)),
        showlegend=leyenda,
        legend=dict(orientation="h", y=1.15, x=0, yanchor="bottom",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
    )
    fig.update_xaxes(showgrid=grid_x, gridcolor=COLOR_GRID, zeroline=False,
                     showline=False, ticks="", tickfont=dict(color=COLOR_TENUE))
    fig.update_yaxes(showgrid=grid_y, gridcolor=COLOR_GRID, zeroline=False,
                     showline=False, ticks="", tickfont=dict(color=COLOR_TENUE))
    return fig
