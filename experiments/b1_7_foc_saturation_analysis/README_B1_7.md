# B1.7 — Saturación vectorial y anti-windup

## Condiciones
- FOC: implementación activa `pmsm_hybrid_control.foc.foc.FOC`.
- dt: 5e-05 s; duración nominal: 0.05 s.
- Referencia id: 0.0 A; referencia iq: 112.43 A.
- Carga: 0.0 Nm.
- VDC experimental provisional: 540.0 V.
- Límite configurado: 296.180688 V.
- La tensión solicitada se captura después del desacoplamiento.
- La tensión aplicada se reconstruye desde va, vb, vc usando Clarke/Park.
- La instrumentación envuelve métodos de la instancia durante la prueba;
  no modifica los módulos de producción.

## Resultados calculados
- Muestras: 1000.
- RMSE global de iq: 55.319630 A.
- Máxima magnitud solicitada dq: 1759.722343 V.
- Máxima magnitud aplicada dq: 296.180688 V.
- Límite configurado: 296.180688 V.
- Muestras marcadas como saturadas: 513.
- Muestras con llamada al anti-windup: 513.
- Máximo exceso aplicado sobre el límite: 0.000000000 V.

## Archivos
- `b1_7_current_tracking.png/pdf`
- `b1_7_voltage_saturation.png/pdf`
- `b1_7_integrators_antiwindup.png/pdf`

CSV fuente: `experiments/b1_7_foc_voltage_saturation.csv`.

## Limitaciones
Este es un ensayo de simulación funcional, no una validación frente a medidas
del motor real. VDC=540 V es provisional. La llamada al anti-windup indica
que se ejecutó el método; no prueba por sí sola que la estrategia sea óptima.
La tensión aplicada reconstruida puede tener pequeñas diferencias numéricas
respecto del límite por transformaciones y redondeo.
