# B1.8 — Recuperación de corriente tras retirar referencia alta

## Objetivo
Observar la respuesta de la planta y del FOC activo al retirar una referencia
alta de corriente. Este ensayo no constituye por sí mismo una validación física.

## Condiciones
- Controlador: `pmsm_hybrid_control.foc.foc.FOC`.
- Paso: 5e-05 s.
- Duración: 0.05 s.
- Referencia id: 0.0 A.
- Referencia iq: 112.43 A antes de 0.025 s; 0.0 A desde ese instante.
- Carga: 0.0 Nm.
- VDC experimental provisional: 540.0 V.
- Límite vectorial configurado: 296.180688 V.
- La referencia alta supera el límite de corriente nominal indicado para el motor;
  se trata de una condición de estrés, no de un punto de operación validado.
- La instrumentación envuelve métodos de esta instancia; no modifica los módulos
  de producción.
- Tensión solicitada: capturada después del desacoplamiento.
- Tensión aplicada: reconstruida desde va, vb, vc mediante Clarke/Park.

## Resultados calculados
- Muestras: 1000.
- RMSE global de iq: 7.067494 A.
- RMSE antes de retirar la referencia: 8.070907 A.
- RMSE durante la recuperación: 5.900852 A.
- iq al primer punto posterior al retiro: 92.084039 A.
- Máximo |iq| durante recuperación: 92.084039 A.
- iq final: 0.074528 A.
- Error absoluto final respecto a 0 A: 0.074528 A.
- Criterio exploratorio de asentamiento: |iq| ≤ 5.0 A de forma sostenida.
- Tiempo hasta cumplir el criterio: 0.300000 ms después del retiro de referencia.
- Máximo |id|: 14.306371 A.
- Máximo |omega_m|: 432.093131 rad/s.
- Máximo |Te|: 72.269395 Nm.
- Máxima magnitud de tensión solicitada: 1698.931520 V.
- Máxima magnitud de tensión aplicada: 296.180688 V.
- Muestras marcadas saturadas: 17.
- Muestras con llamada al anti-windup: 17.
- Exceso máximo de tensión aplicada sobre el límite: 0.000000000 V.

## Archivos generados
- `b1_8_current_recovery.png/pdf`
- `b1_8_voltage_saturation.png/pdf`
- `b1_8_integrators_antiwindup.png/pdf`
- `b1_8_speed_torque.png/pdf`
- CSV fuente: `experiments/b1_8_foc_recovery.csv`.

## Limitaciones e interpretación
La llamada al anti-windup indica ejecución del método, no demuestra por sí sola
que la estrategia mejore el desempeño. La referencia alta es una demanda de
estrés y no debe interpretarse como operación admisible del motor. VDC=540 V
es provisional. La prueba usa la planta simulada y no datos experimentales del
motor real. El umbral de ±5 A es un criterio exploratorio definido para esta
prueba, no una especificación del fabricante.
