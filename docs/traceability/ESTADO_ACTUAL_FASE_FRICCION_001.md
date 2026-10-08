# Punto de control 001 — Etapa de fricción no lineal

**Proyecto:** Digital Twin PMSM Siemens 1FT7087
**Repositorio:** `pmsm-hybrid-control-migracion`
**Rama de referencia:** `main`
**Commit de referencia:** `5f77436`
**Estado remoto:** `main` sincronizada con `origin/main` en el momento del registro
**Etapa:** Caracterización de fricción, evaluación funcional y diagnóstico previo a la especificación ANFIS

---

## 1. Propósito del punto de control

Este documento registra el estado técnico del proyecto antes de continuar con la definición formal de la estrategia de control adaptativo basada en ANFIS.

El punto de control corresponde a una etapa en la que el Digital Twin PMSM ya dispone de una representación de fricción mecánica no lineal y se han realizado ensayos destinados a caracterizar sus efectos sobre la dinámica del accionamiento y sobre el comportamiento del control de velocidad.

La finalidad de esta nota es preservar la separación entre:

- resultados experimentales obtenidos;
- interpretaciones derivadas de dichos resultados;
- hipótesis metodológicas todavía abiertas;
- actividades que aún no han sido ejecutadas.

Este registro no constituye una conclusión final de validación física del motor Siemens 1FT7087 ni una demostración de mejora mediante ANFIS.

---

## 2. Estado del repositorio en el punto de control

Al realizar la inspección del repositorio se obtuvo:

- rama activa: `main`;
- `HEAD`: `5f77436`;
- commit: `Corregir interfaz y actualizar evidencia experimental B1 B2`;
- `main` se encontraba alineada con `origin/main`;
- los artefactos correspondientes a las etapas F y J se encontraban como archivos no seguidos por Git en este punto.

Los archivos experimentales no se incorporan automáticamente a este commit de documentación. Su incorporación, agrupación y eventual selección para el reporte técnico deberán realizarse posteriormente mediante una revisión explícita de evidencia.

En una inspección posterior, el directorio de trabajo también mostró modificaciones
pendientes en archivos versionados de los ensayos B0, del ensayo B2.4, del FOC y de
varios módulos de integración. Estos cambios se consideran trabajo existente y quedan
expresamente fuera del commit de este punto de control. La nota registra el commit
de referencia, pero no implica que el directorio de trabajo esté limpio.


Los artefactos `np` y `pd` observados en el directorio del repositorio quedan fuera de este punto de control y no son modificados.

---

## 3. Estado técnico del Digital Twin

El proyecto utiliza como núcleo el modelo PMSM `M4_BASE`, sobre el cual se han desarrollado progresivamente las capas de control y los escenarios experimentales.

La estructura de trabajo mantiene la separación entre:

1. modelo de planta;
2. dinámica mecánica;
3. fricción;
4. control FOC;
5. lazo de velocidad;
6. estrategias de control avanzado.

El FOC permanece como controlador principal de corriente y como responsable de la generación de las referencias de tensión dentro de la arquitectura establecida.

La futura capa ANFIS se plantea como una capa adaptativa o supervisora sobre la regulación de velocidad y no como sustituto del FOC.

---

## 4. Etapa F — incorporación y caracterización de fricción

La etapa F se desarrolló para estudiar el efecto de una representación de fricción mecánica no lineal sobre la respuesta del Digital Twin.

La representación utilizada tiene la forma general:

\[
T_f(\omega)=
\left[
T_C+
(T_S-T_C)
e^{-(|\omega|/\omega_S)^\delta}
\right]
\operatorname{sgn}(\omega)
+
B\omega
\]

para velocidad distinta de cero, con tratamiento específico del estado de reposo.

Esta estructura permite representar componentes asociadas a fricción de Coulomb, fricción estática/Stribeck y componente viscosa.

### 4.1 Caracterización

Los ensayos F0.x se orientan a:

- caracterizar la contribución de la fricción;
- separar sus componentes;
- identificar regiones de operación relevantes;
- observar el comportamiento alrededor de diferentes regímenes de velocidad.

### 4.2 Evaluación funcional

Los ensayos F1.x estudian el efecto de la fricción sobre:

- la dinámica mecánica;
- el seguimiento de velocidad;
- la acción del FOC con regulación PI;
- la operación a baja velocidad;
- la reversión de velocidad;
- la sensibilidad ante diferentes niveles de fricción.

Los resultados obtenidos se consideran evidencia computacional y funcional del comportamiento del modelo.

No deben interpretarse como validación experimental del motor físico hasta disponer de referencias externas o mediciones correspondientes.

---

## 5. Etapa J — diagnóstico previo a la definición de ANFIS

Después de la caracterización de fricción se inició un diagnóstico destinado a estudiar si variables observables del sistema pueden proporcionar información útil para una estrategia adaptativa.

La representación candidata estudiada utiliza:

\[
z=
[e_\omega,\Delta e_\omega,|i_q|]
\]

donde:

- \(e_\omega\) representa el error de velocidad;
- \(\Delta e_\omega\) representa su variación;
- \(|i_q|\) representa la magnitud de la corriente asociada a la producción de par.

El objetivo de esta etapa no es demostrar todavía la suficiencia de estas entradas para ANFIS, sino estudiar su comportamiento y su capacidad para distinguir condiciones dinámicas diferentes dentro de los escenarios generados.

---

## 6. Resultados de J1

J1 estudió diferentes candidatos de los parámetros del controlador de velocidad bajo varios escenarios de fricción.

Se utilizaron tres configuraciones de referencia del controlador y cuatro escenarios de fricción.

Los resultados mostraron diferencias en error de velocidad y esfuerzo de corriente entre configuraciones y escenarios.

La reconstrucción de la acción del PI presentó consistencia con los datos registrados.

Estos resultados proporcionan evidencia de que el comportamiento observable cambia con la configuración del controlador y con las condiciones de fricción.

No se establece a partir de J1 que una configuración sea óptima de manera general.

---

## 7. Resultados de J2

J2, J2.1, J2.2 y J2.3 constituyen un diagnóstico preliminar de regiones del espacio observable y de su persistencia temporal.

En el conjunto de trayectorias estudiado se identificaron regiones compartidas del espacio:

\[
z=[e_\omega,\Delta e_\omega,|i_q|]
\]

para diferentes escenarios de fricción y, bajo las condiciones analizadas, se observaron diferencias en variables internas del regulador y en su acción de referencia.

Estas diferencias no mostraron una relación monotónica general con el nivel de fricción.

J2.3 mostró además que las regiones analizadas presentan ocupación temporal sostenida dentro de las trayectorias consideradas.

La interpretación correcta de estos resultados es limitada al conjunto de escenarios y trayectorias estudiado.

Por tanto, estos ensayos no demuestran que las variables seleccionadas sean absolutamente suficientes ni absolutamente insuficientes para representar todas las condiciones relevantes de adaptación.

---

## 8. Estado de J3

J3.1 y J3.2 desarrollaron un procedimiento preliminar para estudiar criterios de selección de configuraciones y establecer un protocolo de etiquetado.

El protocolo considera restricciones físicas y métricas de desempeño antes de seleccionar una configuración candidata.

La corriente medida por el modelo se distingue explícitamente de la referencia de corriente utilizada por el controlador.

J3.3 constituye un probe condicionado por estado que compara configuraciones desde estados internos restaurados de manera controlada.

Este ensayo debe considerarse únicamente como un diagnóstico exploratorio.

### J3 no representa todavía entrenamiento ANFIS.

En este punto:

- no se ha entrenado un ANFIS;
- no se ha establecido una base de reglas definitiva;
- no se han fijado de manera definitiva las funciones de membresía;
- no se ha demostrado una mejora de desempeño mediante ANFIS;
- no se ha establecido que las variables candidatas sean las únicas entradas posibles.

---

## 9. Qué está establecido y qué permanece abierto

### Establecido mediante el desarrollo realizado

1. El Digital Twin puede ejecutarse con una representación explícita de fricción mecánica no lineal.
2. La fricción modifica la respuesta mecánica y el comportamiento observable del accionamiento.
3. La respuesta del sistema depende de las condiciones de operación y de la parametrización del controlador.
4. Existen regiones observables en las trayectorias estudiadas donde aparecen diferencias asociadas a las condiciones analizadas.
5. Las variables candidatas de observación presentan ocupación temporal suficiente en los escenarios utilizados para el diagnóstico.

### No establecido todavía

1. Que \(z=[e_\omega,\Delta e_\omega,|i_q|]\) sea suficiente para todas las condiciones de operación.
2. Que estas tres variables sean la única representación adecuada para ANFIS.
3. Que exista una relación monotónica entre fricción y cualquiera de las variables observables.
4. Que una configuración de PI sea globalmente óptima.
5. Que ANFIS mejore el desempeño respecto al PI convencional.
6. Que la estrategia adaptativa sea estable en todo el dominio de operación.
7. Que los resultados computacionales constituyan validación física del motor real.

---

## 10. Estado conceptual de la futura capa ANFIS

La arquitectura de trabajo mantiene como hipótesis una capa adaptativa sobre el lazo de velocidad:

\[
[e_\omega,\Delta e_\omega,|i_q|]
\longrightarrow
[K_p^{adapt},K_i^{adapt}]
\]

seguida por:

\[
\mathrm{PI}_{\omega}
\longrightarrow
i_q^*
\longrightarrow
\mathrm{FOC}
\longrightarrow
\mathrm{PMSM}
\]

La forma exacta de las salidas adaptativas todavía debe decidirse formalmente.

Entre las alternativas consideradas se encuentran:

\[
ANFIS(z)\rightarrow(K_p,K_i)
\]

\[
ANFIS(z)\rightarrow(\Delta K_p,\Delta K_i)
\]

y

\[
K_p=\alpha_pK_{p0},
\qquad
K_i=\alpha_iK_{i0}.
\]

Estas alternativas permanecen abiertas hasta completar la especificación metodológica.

---

## 11. Siguiente etapa

Antes de realizar entrenamiento ANFIS se requiere definir formalmente:

1. variables de entrada y significado físico;
2. universos de discurso;
3. normalización;
4. tipo y número de funciones de membresía;
5. cobertura y solapamiento;
6. inicialización de las funciones de membresía;
7. estructura de reglas;
8. tipo de consecuente e inferencia;
9. variables de salida;
10. límites admisibles de \(K_p\) y \(K_i\);
11. restricciones de operación;
12. mecanismo de adaptación;
13. condiciones de seguridad;
14. protocolo independiente de validación.

La selección de estos elementos deberá distinguir entre conocimiento de ingeniería, decisiones metodológicas y parámetros identificados a partir de datos.

---

## 12. Hipótesis metodológicas abiertas

Se considera como línea de investigación, todavía no demostrada, estudiar si la definición de regiones de operación y restricciones de estabilidad/desempeño puede utilizarse como referencia para establecer límites de las funciones de membresía y del espacio de adaptación.

Esta posibilidad deberá analizarse posteriormente mediante herramientas apropiadas de estabilidad y control no lineal.

No se registra en este punto ninguna afirmación de que las fronteras de estabilidad deban coincidir directamente con las fronteras de las funciones de membresía.

---

## 13. Regla de trazabilidad

A partir de este punto, toda modificación de la estrategia adaptativa deberá conservar:

- origen de los parámetros;
- versión del controlador;
- escenario de simulación;
- condiciones de fricción;
- señales utilizadas;
- criterio de selección;
- métricas obtenidas;
- configuración ANFIS utilizada;
- separación entre entrenamiento y validación.

Las conclusiones sobre mejora de desempeño deberán sustentarse mediante comparación cuantitativa bajo condiciones equivalentes entre:

**Escenario A:** Digital Twin + FOC + PI convencional.

**Escenario B:** Digital Twin + FOC + estrategia adaptativa ANFIS.

La comparación deberá realizarse posteriormente mediante métricas previamente definidas y no mediante observación cualitativa aislada.

---

## 14. Cierre del punto de control

Este punto de control marca el cierre de la etapa de caracterización y diagnóstico inicial de fricción y el inicio de la preparación metodológica para la especificación del control adaptativo.

El proyecto se encuentra, por tanto, en:

**Fricción no lineal → diagnóstico de observabilidad → especificación ANFIS**

y todavía no en la etapa de entrenamiento ni de validación de una estrategia ANFIS.
