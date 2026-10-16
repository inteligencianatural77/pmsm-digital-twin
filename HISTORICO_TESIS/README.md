# HISTORICO_TESIS

Archivos conservados por trazabilidad histórica, fuera del flujo activo de la tesis.

## Estructura

### `exploratorios/`
Scripts de análisis exploratorio que **no están en la tesis final** pero documentan
el proceso de desarrollo:

- `b0_*.py` — Experimentos B0 (validación inicial del modelo)
- `j1_*.py`, `j2_*.py`, `j3_*.py` — Análisis de suficiencia de variables para ANFIS

Estos scripts **no se ejecutan** en el flujo final de la tesis. Se conservan
porque documentan el proceso de exploración.

### `obsoletos/`
Scripts sin uso detectado en la tesis:

- `d08_pre_diagnostico.py` — Diagnóstico pre-experimental
- `report_scripts/generate_latex_data.py` — Placeholder sin datos
- `report_digital_twin_scripts/generate_latex_data.py` — Placeholder sin datos

## Cuándo consultar esta carpeta

- Para entender el desarrollo histórico del proyecto
- Para recuperar ideas descartadas
- **NO** para regenerar figuras o CSVs de la tesis

## Cuándo NO modificar

- Estos archivos se conservan como snapshot histórico
- Si se necesita reactivar alguno, moverlo de vuelta a `experiments/`
