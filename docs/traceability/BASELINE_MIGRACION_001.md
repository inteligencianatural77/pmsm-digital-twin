# BASELINE DE MIGRACIÓN 001

**Proyecto:** PMSM Siemens 1FT7087 – ROM + Sistema de Control Híbrido Neuro-Difuso  
**Etapa:** Migración MATLAB/Simulink → Python  
**Baseline:** 001  
**Fecha:** 2026-09-22  
**Estado:** Congelado para trazabilidad  
**Fuente primaria del modelo:** `skeleton.slx`

---

## 1. Propósito

Este documento establece el estado técnico de referencia para la etapa de migración del modelo histórico de control PMSM desde MATLAB/Simulink hacia Python.

El objetivo de esta etapa es preservar la arquitectura, interfaces, ecuaciones, parámetros y comportamiento documentado del modelo histórico antes de introducir modificaciones, mejoras o nuevas capacidades.

La fuente primaria utilizada para establecer esta referencia es:

`/home/elmismo/Escritorio/Resultado_001_Validacion_Inicial/skeleton.slx`

Este baseline no constituye una validación física definitiva del PMSM Siemens 1FT7087.

Tampoco constituye una reconciliación definitiva de todos los parámetros históricos encontrados en los diferentes artefactos del proyecto.

La finalidad de este documento es establecer una referencia técnica trazable que permita distinguir claramente entre:

- la fuente histórica;
- la implementación Python migrada;
- las verificaciones realizadas;
- las discrepancias todavía abiertas;
- las modificaciones que se realicen posteriormente.

---

## 2. Fuente histórica

La fuente primaria del modelo histórico es:

`/home/elmismo/Escritorio/Resultado_001_Validacion_Inicial/skeleton.slx`

El directorio histórico asociado contiene:

- `analisis_resultados.md`
- `build_architecture_origen.m`
- `buses.mat`
- `define_buses.m`
- `figura_01.png`
- `figura_02.png`
- `figura_03.png`
- `figura_04.png`
- `figura_05.png`
- `figura_06.png`
- `figura_07.png`
- `motor_params.m`
- `motor_params.mat`
- `plot_results.m`
- `run_simulation.m`
- `README.md`
- `sim_results.mat`
- `skeleton.slx`

Los archivos `.m`, `.mat`, figuras y documentos se consideran material histórico de apoyo y evidencia.

Cuando existe una diferencia entre un archivo auxiliar y el comportamiento o las ecuaciones extraídas directamente de `skeleton.slx`, la diferencia se registra como discrepancia de trazabilidad.

No se realizan correcciones automáticas de esas discrepancias en este baseline.

---

## 3. Arquitectura histórica

La arquitectura identificada en `skeleton.slx` está organizada en los siguientes módulos:

| Módulo | Función |
|---|---|
| M1 | Instrumentación |
| M2 | Power Converter |
| M3 | Electrical Interface |
| M4 | Physical Plant |
| M5 | Validation |
| M6 | Control |
| M7 | Intelligent Supervision |

La cadena funcional principal es:

`REF_BUS → M6 FOC → M3 Electrical Interface → M2 Power Converter → M4 Physical Plant → Feedback`

La arquitectura también contiene buses de referencia, estado, control, adaptación y seguridad.

---

## 4. M3 - Electrical Interface

La implementación identificada en `chart_33.xml` corresponde a la función `electrical_core`.

Sus funciones principales son:

- transformación Clarke;
- transformación Park;
- transformación inversa dq a abc;
- generación de señales de duty;
- limitación de duty;
- generación de señales booleanas de gate;
- cálculo de magnitud de tensión;
- propagación de estados.

El número de pares de polos utilizado es:

`P = 4`

La transformación de corriente implementada es:

`i_alpha = ia`

`i_beta = (ia + 2*ib) / sqrt(3)`

`id = i_alpha*cos(theta_e) + i_beta*sin(theta_e)`

`iq = -i_alpha*sin(theta_e) + i_beta*cos(theta_e)`

La transformación inversa de tensión es:

`V_alpha = Vd*cos(theta_e) - Vq*sin(theta_e)`

`V_beta = Vd*sin(theta_e) + Vq*cos(theta_e)`

Las tensiones de fase se obtienen mediante:

`Va = V_alpha`

`Vb = (-V_alpha + sqrt(3)*V_beta) / 2`

`Vc = (-V_alpha - sqrt(3)*V_beta) / 2`

Los duty se calculan mediante:

`DUTY_A = 0.5 + Va/VDC`

`DUTY_B = 0.5 + Vb/VDC`

`DUTY_C = 0.5 + Vc/VDC`

Cada duty se limita al intervalo:

`0 <= DUTY <= 1`

Los gates se generan mediante:

`GATE_A = DUTY_A > 0.5`

`GATE_B = DUTY_B > 0.5`

`GATE_C = DUTY_C > 0.5`

Esta implementación corresponde a una interfaz simplificada de modulación.

No debe interpretarse como una implementación detallada de SVPWM con sectores, tiempos de conmutación y secuencias explícitas de vectores.

---

## 5. M4 - Physical Plant

La función identificada en `chart_80.xml` es `pmsm_model`.

Los parámetros extraídos directamente del modelo son:

| Parámetro | Valor |
|---|---:|
| Rs | 0.0500 ohm |
| Ld | 0.001200 H |
| Lq | 0.001200 H |
| lambda_f | 0.1100 Wb |
| P | 4 pares de polos |
| J | 0.004160 kg m2 |
| B | 0.0010 |
| T_fric | 0.50 Nm |
| Ts | 0.000050 s |

Las tensiones de fase se calculan mediante:

`Va = (DUTY_A - 0.5)*VDC_in`

`Vb = (DUTY_B - 0.5)*VDC_in`

`Vc = (DUTY_C - 0.5)*VDC_in`

La velocidad eléctrica es:

`omega_e = P*omega_m`

Las ecuaciones eléctricas son:

`did = (Vd - Rs*id + omega_e*Lq*iq)/Ld`

`diq = (Vq - Rs*iq - omega_e*(Ld*id + lambda_f))/Lq`

La actualización de corriente utiliza Euler explícito:

`id(k+1) = id(k) + did*Ts`

`iq(k+1) = iq(k) + diq*Ts`

El par electromagnético implementado es:

`Te = 1.5*P*lambda_f*iq`

La dinámica mecánica es:

`domega = (Te - Tl - B*omega_m - T_fric*sign(omega_m))/J`

La actualización de velocidad es:

`omega_m(k+1) = omega_m(k) + domega*Ts`

La posición mecánica se actualiza mediante:

`theta_m(k+1) = theta_m(k) + omega_m(k+1)*Ts`

El modelo contiene además una estimación térmica simplificada:

`T_winding = 20 + 80*(id^2 + iq^2)*Rs/1000`

Este modelo representa una planta PMSM concentrada y analítica.

No representa en esta etapa una reconstrucción FEM distribuida del motor.

---

## 6. M6 - FOC Controller

La implementación identificada en `chart_66.xml` corresponde a `foc_core`.

Parámetros de los controladores de corriente:

| Parámetro | Valor |
|---|---:|
| Kp_id | 15.0796 |
| Ki_id | 628.3185 |
| Kp_iq | 15.0796 |
| Ki_iq | 628.3185 |
| Ts corriente | 50 us |

Parámetros del controlador de velocidad:

| Parámetro | Valor |
|---|---:|
| Kp_w | 5.2804 |
| Ki_w | 1.2693 |
| Ts velocidad | 200 us |

Otros parámetros:

| Parámetro | Valor |
|---|---:|
| Ld | 0.001200 H |
| Lq | 0.001200 H |
| lambda_f | 0.1100 Wb |
| P | 4 |
| id_ref | 0 |
| iq_max | 112.4300 A |
| iq_min | -112.4300 A |

El lazo de velocidad se ejecuta cada cuatro pasos del lazo de corriente:

`Ts_s/Ts_c = 200 us/50 us = 4`

El controlador contiene:

- PI de corriente d;
- PI de corriente q;
- PI de velocidad;
- desacoplamiento d/q;
- feedforward asociado al flujo;
- saturación de tensión;
- anti-windup.

El límite de tensión utilizado es:

`V_max = VDC/sqrt(3)*0.95`

La referencia de corriente d es:

`id_ref = 0`

La referencia de corriente q se limita a:

`-112.43 A <= iq_ref <= 112.43 A`

---

## 7. M2 - Power Converter

M2 constituye la interfaz de conversión de potencia entre M3 y M4.

En la reconstrucción Python actual, M2 se representa mediante una interfaz ideal o passthrough.

Esto permite reproducir la cadena funcional del modelo histórico sin introducir todavía un modelo detallado de:

- interruptores;
- pérdidas de conmutación;
- tiempos muertos;
- PWM físico;
- impedancias parasitarias;
- dinámica del bus DC.

Esta simplificación pertenece a la reconstrucción funcional y no debe confundirse con una representación física completa del convertidor.

---

## 8. M5 - Validation

M5 corresponde principalmente a la capa de observación, visualización y registro.

Entre las señales identificadas se encuentran:

- `omega_m`
- `omega_ref`
- `iq`
- `iq_ref`
- `safety_mode`

También se identifican los registros:

- `omega_m_log`
- `iq_log`

Los elementos de visualización incluyen scopes asociados a:

- velocidad;
- corrientes;
- tensiones;
- seguridad.

M5 se considera una capa de observabilidad y evidencia.

No se considera el origen principal de la dinámica del PMSM ni del controlador FOC.

---

## 9. M7 - Intelligent Supervision

M7 contiene la arquitectura destinada a las funciones inteligentes y de supervisión.

Se identifican los bloques:

- `ANFIS_Adaptativo`
- `FIS_Supervisor`
- `Guardian_Lyapunov`

También se identifican buses relacionados con:

- `ADAPT_BUS`
- `SAFETY_BUS`

El análisis de `skeleton.slx` muestra que estos elementos corresponden principalmente a una arquitectura preparada para dichas funciones.

Por tanto, en este baseline no deben considerarse como una implementación completa y validada de:

- ANFIS;
- FIS supervisor;
- MPC;
- Guardian Lyapunov.

La existencia de estos bloques demuestra la intención arquitectónica del sistema, pero no constituye por sí sola evidencia de una implementación funcional completa.

---

## 10. REF_BUS

El modelo histórico utiliza un bus de referencias que contiene señales como:

- `id_ref`
- `iq_ref`
- `modo_operacion`
- `Kp_adapt`
- `Ki_adapt`
- `omega_ref`

La arquitectura permite compartir estas referencias entre los módulos de control y supervisión.

Entre los valores identificados se encuentran:

`id_ref = 0`

`omega_ref = motor.omega_nominal`

`Kp_adapt = anfis.Kp_base`

`Ki_adapt = anfis.Ki_base`

Estas interfaces se conservan como parte del contrato arquitectónico de la migración.

---

## 11. Escenario histórico

Dentro de M4 se identificó directamente un bloque de carga denominado `Tl_step`.

Su configuración es:

`Time = 1.0 s`

`After = 23 Nm`

Por lo tanto, el modelo `skeleton.slx` contiene directamente un escalón de carga de 23 Nm a partir de 1 segundo.

El `README.md` histórico asociado describe además un escenario que incluye:

- velocidad nominal aproximada de 4500 rpm;
- rampa inicial;
- carga de 23 Nm;
- perturbación de VDC;
- inversión de velocidad;
- duración de 3 segundos;
- paso temporal de 50 us;
- método ode4.

Estos elementos se consideran documentación histórica.

La configuración interna encontrada en `skeleton.slx` presenta discrepancias con esa descripción y se documenta en la sección siguiente.

---

## 12. Configuración del solver

El archivo interno `configSet0.xml` de `skeleton.slx` contiene:

`StartTime = 0.0`

`StopTime = 10.0`

`FixedStep = auto`

`SolverName = VariableStepAuto`

`ODEIntegrationMethod = ode3`

Esta configuración presenta una discrepancia con el `README.md` histórico, que describe:

`Fixed step = 50 us`

`ode4`

También existe una discrepancia con `run_simulation.m`, que implementa la simulación mediante actualización explícita tipo Euler.

Por tanto, existen tres referencias de integración temporal:

| Fuente | Configuración |
|---|---|
| `skeleton.slx` | VariableStepAuto / ode3 |
| `README.md` | Fixed step 50 us / ode4 |
| `run_simulation.m` | Actualización explícita tipo Euler |

Esta diferencia queda registrada como hallazgo de trazabilidad.

No se corrige en este baseline.

---

## 13. Parámetros históricos con discrepancias

Se identificaron diferencias entre los parámetros directamente extraídos de `skeleton.slx`, `motor_params.m` y `analisis_resultados.md`.

Ejemplos:

| Parámetro | skeleton.slx | motor_params.m | analisis_resultados.md |
|---|---:|---:|---:|
| Rs | 0.050 ohm | 0.050 ohm | 0.120 ohm |
| Ld | 0.001200 H | 0.001200 H | 0.000450 H |
| Lq | 0.001200 H | 0.001200 H | 0.000650 H |
| lambda_f | 0.110 Wb | 0.110 Wb | 0.110 Wb |
| P | 4 | 4 | 6 |
| J | 0.004160 | 0.004160 | 0.001680 |
| B | 0.0010 | 0.0010 | 0.0001 |
| T_fric | 0.50 Nm | 0.50 Nm | 0.10 Nm |

Estas diferencias no se consideran errores que deban corregirse dentro de este baseline.

Se registran como discrepancias históricas que deberán resolverse posteriormente mediante trazabilidad documental y análisis técnico.

---

## 14. Reconstrucción Python

La implementación Python existente se encuentra en:

`closed_loop_reconstruction/lazo_cerrado_m3_foc_m4.py`

La reconstrucción reproduce funcionalmente la cadena:

`M3 → M6 → M3 → M2 → M4 → feedback`

La implementación utiliza los parámetros y ecuaciones principales identificados directamente en `skeleton.slx`.

El objetivo de esta implementación es:

- recuperar el comportamiento computacional;
- conservar las interfaces funcionales;
- permitir ejecución sin MATLAB;
- establecer una base reproducible;
- preparar la integración posterior del sistema neuro-difuso.

La implementación Python no debe interpretarse como una demostración de equivalencia numérica completa entre MATLAB/Simulink y Python.

---

## 15. Reproducibilidad Python

La reconstrucción Python ha sido ejecutada de forma determinista.

Se verificó que dos ejecuciones independientes producen archivos CSV byte-identical.

Hashes registrados:

Modelo:

`ad85691c8e3c62955f48264c718353ba0368b2ac4c749a3317f4bbb34ce508f8`

CSV:

`5d3e079ea8c9e39ba293f5b42e0d5982018e85946b694a8d0c153fe8e946eaf0`

Generador de gráficas:

`729cb85a1323bb79f962d706451fa1bb043cb32d44ea212655c58c6d0553ab71`

También se verificó la generación reproducible de las siete figuras existentes en:

`closed_loop_reconstruction/figuras/`

---

## 16. Estado actual de validación

| Elemento | Estado |
|---|---|
| Identificación de fuente histórica | Confirmada |
| Extracción de arquitectura | Confirmada |
| Extracción de M3 | Confirmada |
| Extracción de M4 | Confirmada |
| Extracción de M6 | Confirmada |
| Identificación de M7 | Confirmada |
| Reconstrucción funcional Python | Confirmada |
| Reproducibilidad Python | Confirmada |
| Equivalencia numérica MATLAB/Python | Pendiente |
| Validación física Siemens | Pendiente |
| Validación FEM distribuida | Fuera del alcance actual |
| ANFIS funcional en Python | Pendiente |
| Integración Tiny + sistema neuro-difuso | Pendiente |

---

## 17. Alcance de la etapa actual

La etapa actual sigue la siguiente secuencia:

`Fuente histórica → Arquitectura → Ecuaciones → Interfaces → Reconstrucción Python → Reproducibilidad → Validación → Sistema híbrido neuro-difuso`

Durante esta etapa no se modifica:

- la geometría histórica;
- el STEP histórico;
- el modelo FEM distribuido;
- `pmsm_K3`;
- `pmsm_Cloude`;
- la arquitectura histórica de forma destructiva;
- los parámetros históricos para corregirlos sin evidencia.

La prioridad es recuperar y formalizar la base concentrada y analítica ya existente.

---

## 18. Decisiones de trazabilidad

### DEC-MIG-001

La fuente primaria de la migración es `skeleton.slx`.

### DEC-MIG-002

La reconstrucción Python debe preservar primero la arquitectura y los contratos antes de introducir mejoras algorítmicas.

### DEC-MIG-003

Las discrepancias entre parámetros y artefactos históricos deben registrarse antes de realizar cualquier corrección.

### DEC-MIG-004

La ausencia de MATLAB no debe impedir la continuidad del desarrollo y validación en Python.

### DEC-MIG-005

La reconstrucción concentrada y analítica tiene prioridad durante esta etapa sobre la reconstrucción FEM distribuida.

### DEC-MIG-006

La ANFIS y el sistema neuro-difuso se incorporarán posteriormente sobre una base Python reproducible.

---

## 19. Elementos pendientes

Quedan pendientes:

1. Verificar la equivalencia numérica contra una ejecución reproducible de `skeleton.slx`, cuando sea posible.
2. Resolver las discrepancias entre `skeleton.slx`, `motor_params.m`, `analisis_resultados.md` y otros artefactos.
3. Formalizar los contratos Python de M3, M4, M6 y M7.
4. Separar claramente el modelo PMSM, el FOC y el sistema neuro-difuso.
5. Implementar y verificar las no linealidades necesarias para ANFIS.
6. Definir el módulo Tiny y sus interfaces.
7. Integrar ANFIS/Tiny sin alterar la referencia histórica.
8. Automatizar la validación, métricas, figuras y documentación LaTeX.

---

## 20. Regla de modificación posterior

Toda modificación posterior que altere cualquiera de los siguientes elementos:

- ecuaciones;
- parámetros;
- interfaces;
- arquitectura;
- solver;
- señales;
- controladores;
- comportamiento;

deberá quedar registrada como un cambio posterior al baseline.

Este documento representa una fotografía técnica congelada de la etapa de migración al 2026-09-22.

Cualquier mejora posterior deberá poder distinguirse claramente de esta referencia.

---

## 21. Referencia Git

Repositorio local:

`pmsm-hybrid-control-migracion`

Rama de referencia:

`main`

La reconstrucción Python se encuentra actualmente en:

`closed_loop_reconstruction/`

Este documento establece la primera referencia formal de trazabilidad de la migración.

---

# Fin de BASELINE_MIGRACION_001
