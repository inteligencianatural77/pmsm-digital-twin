"""Plantilla para convertir resultados reproducibles de Python a macros LaTeX.

No contiene todavía métricas del proyecto. Se completará cuando quede fijado
el experimento de referencia y su formato de salida.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "datos" / "resultados_pmsm.tex"
OUT.parent.mkdir(parents=True, exist_ok=True)

content = r'''% ESTE ARCHIVO ES GENERADO AUTOMÁTICAMENTE. NO EDITAR A MANO.
% \newcommand{\OmegaFinal}{...}
% \newcommand{\RMSEVel}{...}
'''

OUT.write_text(content, encoding="utf-8")
print(f"Generado: {OUT}")
