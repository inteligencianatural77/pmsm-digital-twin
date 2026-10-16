# Cierre B1.7–B1.8 — FOC

## Estado
- 18 pruebas unitarias aprobadas.
- B1.7: saturación de tensión con referencia alta sostenida.
- B1.8: recuperación de corriente tras retirar la referencia.
- Ambos ensayos son simulaciones; no constituyen validación física.

## B1.7 — Saturación
- Paso temporal: 50 us; duración: 50 ms.
- Referencia: id = 0 A, iq = 112.43 A.
- VDC provisional: 540 V; límite vectorial: 296.180688 V.
- RMSE de iq: 55.319630 A.
- Tensión solicitada máxima: 1759.722343 V.
- Tensión aplicada máxima: 296.180688 V.
- Muestras saturadas: 513; llamadas al anti-windup: 513.
- iq final: 17.034977 A.
- Interpretación: la tensión quedó limitada, pero el seguimiento de la referencia alta fue deficiente.

## B1.8 — Recuperación
- Paso temporal: 50 us; duración: 50 ms.
- iq_ref: 112.43 A antes de 25 ms; 0 A desde 25 ms.
- VDC provisional: 540 V; límite vectorial: 296.180688 V.
- RMSE global de iq: 7.067494 A.
- iq al retirar la referencia: 92.084039 A.
- iq final: 0.074528 A.
- Asentamiento dentro de ±5 A: 0.300 ms tras retirar la referencia.
- Muestras saturadas: 17; llamadas al anti-windup: 17.
- Interpretación: iq volvió cerca de cero bajo las condiciones simuladas. El resultado no aísla el efecto del anti-windup.

## Pruebas automatizadas
Se ejecutaron:
- pmsm_hybrid_control/tests/test_current_controller.py
- pmsm_hybrid_control/tests/test_foc_current.py

Resultado: 18 passed in 0.12s.

## Artefactos
B1.7:
- experiments/b1_7_foc_voltage_saturation_instrumented.py
- experiments/b1_7_foc_voltage_saturation.csv
- experiments/b1_7_foc_saturation_analysis/

B1.8:
- experiments/b1_8_foc_recovery_instrumented.py
- experiments/b1_8_foc_recovery.csv
- experiments/b1_8_foc_recovery_analysis/

## Limitaciones
- VDC = 540 V es provisional.
- La referencia de 112.43 A es una condición de estrés, no un punto de operación validado.
- Los ensayos usan una planta simulada, no mediciones del motor real.
- Las llamadas al anti-windup no demuestran por sí solas su eficacia.
- Estos resultados no prueban estabilidad global ni validación física.

## Estado de cierre
B1.7 y B1.8 quedan documentados como evidencia exploratoria de simulación.
No se modificaron los módulos de producción ni se creó un commit.
