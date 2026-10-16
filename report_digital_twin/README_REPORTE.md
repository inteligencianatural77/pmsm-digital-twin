# Reporte técnico PMSM — estructura base

Esta carpeta contiene la estructura inicial del reporte para editarse desde VS Code.

## Flujo conceptual

Python -> validación/repetición -> refinamiento -> Simulink/Simscape para implementación.

`skeleton.slx` es referencia histórica/temporal de arquitectura y trazabilidad; no es la especificación permanente del sistema.

## Regla de resultados

Los resultados experimentales no deben escribirse manualmente en `main.tex` ni en los capítulos. Python debe generar datos consumibles por LaTeX en `datos/*.tex` y figuras en `figuras/`.

## Prioridad técnica

FOC = controlador principal establecido.

ANFIS + MPC + Tiny/TinyML = capa de desarrollo inteligente, aún en desarrollo.

Los contratos de frontera son una especificación arquitectónica independiente de la organización del repositorio.
