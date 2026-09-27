# B0 — Baseline funcional de validación
## Caso STEP23 — 20 s

**Estado:** baseline de referencia experimental  
**Propósito:** establecer una referencia reproducible para futuras modificaciones y comparaciones.  
**No representa:** la configuración definitiva del modelo ni del controlador.

---

## 1. Identificación

- Baseline: B0
- Caso: STEP23
- Duración: 20 s
- Fecha de cierre: 2026-09-25 14:51:09 -0600
- Git HEAD: `1cfb36d8951eb11bdaab1a355ea2abef3dd248a5`

### Estado del árbol Git al cierre

```text
?? .venv_pre_migracion_pathfix/
?? 0
?? pmsm_hybrid_control/
?? results/
```

---

## 2. Escenario de simulación

| Parámetro | Valor |
|---|---:|
| Paso de integración | 5e-5 s |
| Frecuencia equivalente | 20 kHz |
| Duración | 20 s |
| VDC | 540 V |
| Referencia de velocidad | 157.079633 rad/s |
| Carga inicial | 0 Nm |
| Evento de carga | 0.05 s |
| Carga posterior | 23 Nm |

El escenario constituye una condición de validación/referencia y podrá modificarse posteriormente.

---

## 3. Arquitectura B0

```text
Referencia de velocidad
        ↓
FOC
        ↓
M3 / transformaciones
        ↓
PMSM
        ↓
retroalimentación
        ↺
```

En B0:

- FOC permanece como controlador principal.
- La planta PMSM está separada conceptualmente de los parámetros del FOC.
- No se utiliza ANFIS como controlador.
- No se utiliza MPC.
- La capa inteligente queda fuera de este baseline.
- `skeleton.slx` permanece como referencia histórica/arquitectónica, no como especificación permanente.

---

## 4. Parámetros de planta utilizados

| Parámetro | Valor / estado |
|---|---:|
| Rs | 0.05 Ohm |
| Ld | 0.0012 H |
| Lq | 0.0012 H |
| lambda_m | 0.107245 Wb |
| pares de polos | 4 |
| J | 0.00416 kg·m² |
| B | pendiente |
| Tfric | pendiente |

Los parámetros B y Tfric no se rellenan con valores históricos no confirmados.

---

## 5. Parámetros relevantes del FOC B0

| Parámetro | Valor |
|---|---:|
| Kp corriente | 15.0796 |
| Ki corriente | 628.3185 |
| Kp velocidad | 5.2804 |
| Ki velocidad | 1.2693 |
| limite iq_ref | ±112.43 A |

**Nota:** el límite de ±112.43 A corresponde a `iq_ref`, no a una limitación dura de la corriente física.

En esta ejecución:

- `iq_max_abs = 120.2163 A`
- `iq_ref_max_abs = 112.43 A`

La diferencia queda registrada como comportamiento transitorio del lazo de corriente y como punto de refinamiento futuro.

---

## 6. Resultados principales

| Métrica | Resultado |
|---|---:|
| omega final | 157.023729215 rad/s |
| error final | 0.055903785 rad/s |
| error relativo final | 0.035589454 % |
| RMS error velocidad | 2.991264054 rad/s |
| settling 1 % | 6.12635 s |
| iq final | 35.743789011 A |
| iq_ref final | 35.761422088 A |
| error iq final | 0.017633076 A |
| Te final | 23.000055915 Nm |
| Te - Tload final | 0.000055915 Nm |
| Vdq máximo | 296.184293203 V |
| duty mínimo | 0.025 |
| duty máximo | 0.976642687 |
| muestras PWM fuera de [0,1] | 0 |

---

## 7. Evento de carga

En t = 0.05 s se aplica el cambio:

```text
Tload: 0 Nm → 23 Nm
```

Valores observados:

| Magnitud | Antes | Evento | Después |
|---|---:|---:|---:|
| omega | 157.078502 | 157.078775 | 153.026211 rad/s |
| iq | 0.001822 | 0.001747 | 19.756613 A |
| Te | 0.001172 | 0.001124 | 12.712788 Nm |

La respuesta transitoria y la recuperación forman parte de la evidencia de B0.

---

## 8. Artefactos de evidencia

### Trayectoria completa

`results/b0/step23_20s/trajectory.csv`

- 400000 muestras
- SHA-256: `68c89e3d88ed51d18dd9fe07061d1185169aa95c7dd6a43846d1ba173b914278`

### Métricas

`results/b0/step23_20s/metrics.csv`

- SHA-256: `c0f4fc2e56430b912089660173a18db8808bd6a42512e1691c977a68b1a002ea`

### Figuras

`results/b0/step23_20s/figuras/`

1. `01_velocidad_0_20s.png`
2. `02_evento_carga_velocidad.png`
3. `03_evento_carga_corriente_torque.png`
4. `04_regimen_final_velocidad.png`
5. `05_regimen_final_error.png`
6. `06_regimen_final_corrientes.png`
7. `07_regimen_final_torque.png`
8. `08_regimen_final_voltaje.png`
9. `09_regimen_final_pwm.png`

Las nueve figuras fueron revisadas visualmente y consideradas correctas para esta ejecución.

---

## 9. Discrepancias y pendientes conocidas

### 9.1 Flujo magnético

Existe una diferencia histórica entre:

```text
lambda_m planta confirmada = 0.107245 Wb
lambda_m histórico FOC     = 0.1100 Wb
```

No se resuelve dentro de B0.

### 9.2 Límite de corriente

```text
Imax oficial          = 79.5 A
limite iq_ref B0      = ±112.43 A
iq máximo observado   = 120.216 A
```

La discrepancia queda registrada para una fase posterior de armonización.

### 9.3 Fricción

```text
B      = pendiente
Tfric  = pendiente
```

No se incorporan valores históricos no confirmados.

---

## 10. Alcance del baseline

B0 se considera:

**válido como referencia funcional y de validación**, pero:

- no es la configuración final;
- no congela los parámetros futuros;
- no cierra todavía todos los parámetros físicos de la planta;
- no representa la arquitectura inteligente final;
- no constituye la especificación permanente del sistema.

Su función principal es permitir comparar futuras modificaciones contra una ejecución conocida.

---

## 11. Regla de comparación futura

Cualquier nueva variante deberá poder identificarse respecto de B0 indicando explícitamente:

1. qué parámetro cambió;
2. qué bloque cambió;
3. qué condición de simulación cambió;
4. qué resultados cambiaron;
5. qué métricas mejoraron, empeoraron o permanecieron equivalentes.

B0 se conserva como referencia y no se modifica retrospectivamente.

---

## 12. Principio de desarrollo posterior

La evolución prevista es:

```text
B0
 ↓
refinamiento de planta / FOC
 ↓
nuevo baseline si corresponde
 ↓
extensión inteligente
 ↓
comparación controlada contra baseline
```

La introducción de una capa inteligente no sustituye al FOC como controlador principal.

---

## 13. Estado

**B0 — CERRADO COMO BASELINE EXPERIMENTAL**

La configuración podrá cambiar en fases posteriores; los cambios deberán generar una nueva variante o baseline identificable.

