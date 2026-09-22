# PMSM Hybrid Control — Recuperación Python

## 1. Propósito

Este repositorio contiene una reconstrucción Python reproducible del lazo cerrado de control PMSM basado en la arquitectura M3 + FOC + M4 recuperada del proyecto original.

El objetivo de esta etapa es disponer de una base ejecutable, determinista y trazable para continuar posteriormente con la evolución del sistema de control.

> **Alcance:** este modelo es una reconstrucción funcional en Python. Los resultados obtenidos en esta etapa no constituyen por sí mismos una validación física del motor Siemens 1FT7087.

---

## 2. Modelo reproducible

El experimento principal se encuentra en:

```text
closed_loop_reconstruction/lazo_cerrado_m3_foc_m4.py
```

La cadena reproducible es:

```text
lazo_cerrado_m3_foc_m4.py
        │
        ▼
resultado_lazo_cerrado.csv
        │
        ▼
generar_graficas.py
        │
        ▼
7 gráficas PNG
```

### Estructura

```text
closed_loop_reconstruction/
├── lazo_cerrado_m3_foc_m4.py
├── resultado_lazo_cerrado.csv
├── generar_graficas.py
├── figuras/
│   ├── 01_velocidad.png
│   ├── 02_error_velocidad.png
│   ├── 03_corrientes_dq.png
│   ├── 04_torque.png
│   ├── 05_tensiones_dq.png
│   ├── 06_duty.png
│   └── 07_iq_limites.png
└── figuras_hoy.zip
```

---

## 3. Ejecución

Activar el entorno Python:

```bash
source .venv/bin/activate
```

Ejecutar el modelo:

```bash
python closed_loop_reconstruction/lazo_cerrado_m3_foc_m4.py
```

El modelo genera:

```text
closed_loop_reconstruction/resultado_lazo_cerrado.csv
```

Después, generar las gráficas:

```bash
python closed_loop_reconstruction/generar_graficas.py
```

Las figuras se guardan en:

```text
closed_loop_reconstruction/figuras/
```

---

## 4. Configuración principal

Los parámetros principales utilizados por el modelo son:

| Parámetro               |                Valor |
| ----------------------- | -------------------: |
| Rs                      |             0.0500 Ω |
| Ld                      |           0.001200 H |
| Lq                      |           0.001200 H |
| λm                      |            0.1100 Wb |
| J                       |       0.004160 kg·m² |
| VDC                     |                600 V |
| Ts_c                    |                50 µs |
| Ts_s                    |               200 µs |
| iq_max                  |             112.43 A |
| iq_min                  |            -112.43 A |
| referencia de velocidad | 157.0796326795 rad/s |

El modelo utiliza `Ld = Lq`, por lo que la contribución de torque de reluctancia es nula en esta formulación.

---

## 5. Experimento

La simulación tiene una duración de aproximadamente:

```text
3 s
```

La referencia de velocidad corresponde a:

```text
157.0796326795 rad/s
```

Durante el experimento se aplica una carga de:

```text
23 Nm
```

a partir de:

```text
t = 1 s
```

El experimento fue ejecutado dos veces y produjo el mismo CSV byte a byte.

---

## 6. Resultado final

Al final de la simulación:

| Variable           |        Resultado |
| ------------------ | ---------------: |
| ωref               | 157.079633 rad/s |
| ωm                 | 152.906868 rad/s |
| error de velocidad |   4.172765 rad/s |
| id                 |      -1.096502 A |
| iq                 |      35.844059 A |
| iq_ref             |      35.860810 A |
| Te                 |     23.657079 Nm |
| Tload              |     23.000000 Nm |
| Vd                 |     -26.362679 V |
| Vq                 |      68.266423 V |
| VDC                |            600 V |

Estos valores describen el comportamiento del modelo reproducible bajo las condiciones del experimento.

---

## 7. Gráficas

El generador produce siete salidas:

1. Velocidad mecánica y referencia.
2. Error de velocidad.
3. Corrientes `d-q`.
4. Torque electromagnético y torque de carga.
5. Tensiones `d-q`.
6. Duty cycles.
7. `iq` y límites de corriente.

La generación de estas figuras ya está automatizada y forma parte del repositorio.

---

## 8. Reproducibilidad

Identificadores SHA-256 de la versión utilizada:

```text
Modelo:
ad85691c8e3c62955f48264c718353ba0368b2ac4c749a3317f4bbb34ce508f8

CSV:
5d3e079ea9c8e39ba293f5b42e0d5982018e85946b694a8d0c153fe8e946eaf0

Generador de gráficas:
729cb85a1323bb79f962d706451fa1bb043cb32d44ea212655c58c6d0553ab71
```

La repetición del experimento produjo:

```text
cmp = 0
```

por lo que las dos ejecuciones comparadas generaron archivos CSV idénticos.

---

## 9. Estado y limitaciones

Esta etapa establece una base reproducible para el desarrollo posterior.

Queda fuera del alcance de esta versión:

* validación experimental contra el motor físico;
* validación definitiva de curvas Siemens;
* identificación completa de parámetros electromagnéticos;
* modelo FEM distribuido;
* mapas no lineales de flujo y torque;
* entrenamiento ANFIS;
* integración del módulo Tiny;
* modelo térmico validado.

La reconstrucción debe considerarse una **base funcional de simulación**, no un gemelo físico validado del Siemens 1FT7087.

---

## 10. Estado del desarrollo

Ruta de desarrollo:

```text
P0  Repositorio y respaldo                 [OK]
P1  Punto de recuperación Git              [OK]
P2  Modelo Python reproducible             [OK]
P3  Experimento reproducible               [OK]
P4  CSV + generación reproducible          [OK]
P5  Documentación mínima                   [EN CURSO]
P6  Estructura PI digital                  [PENDIENTE]
P7  Automatización de informe              [PENDIENTE]
P8  ANFIS / no linealidades avanzadas      [PENDIENTE]
```

El directorio `pmsm_hybrid_control/` permanece fuera del conjunto rastreado de este repositorio en esta etapa y no forma parte del experimento reproducible descrito aquí.
