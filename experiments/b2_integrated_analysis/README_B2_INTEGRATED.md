# Figuras integradas B2.2–B2.3

## Procedencia
Las figuras se generaron con `experiments/plot_b2_integrated_results.py`
a partir de los CSV existentes. No se volvió a ejecutar la simulación
ni se modificaron los módulos del controlador o de la planta.

## B2.2 — Lazo cerrado de velocidad
- CSV: `experiments/b2_2_speed_closed_loop.csv`
- Muestras: 4000
- Paso temporal: 50 us
- Duración nominal: 200 ms
- Referencia de velocidad: 0 rad/s y después 100 rad/s desde 50 ms.
- Carga: 0 Nm.

Figuras: velocidad, corriente q, par electromagnético y tensiones trifásicas.

## B2.3 — Lazo de velocidad con escalones de carga
- CSV: `experiments/b2_3_speed_load_steps.csv`
- Muestras: 4000
- Paso temporal: 50 us
- Duración nominal: 200 ms
- Referencia de velocidad: 100 rad/s.
- Carga: 0 Nm desde el inicio; 5 Nm a 100 ms; 10 Nm a 150 ms;
  5 Nm a 175 ms.

Figuras: velocidad, corriente q, par electromagnético y tensiones trifásicas.
La figura de par incluye también el par de carga.

## Limitaciones
- Son resultados de simulación, no mediciones experimentales del motor real.
- La referencia de corriente llega aproximadamente a 112.43 A; no debe
  interpretarse como un punto nominal validado del motor.
- Las tensiones trifásicas registradas no permiten verificar por sí solas
  el límite vectorial d-q ni la acción del anti-windup.
- El RMSE global de velocidad incluye el arranque desde cero.
- Las figuras no demuestran por sí solas estabilidad global ni validación
  física del Digital Twin.

## Archivos
Cada figura se conserva en PNG y PDF en este directorio.
