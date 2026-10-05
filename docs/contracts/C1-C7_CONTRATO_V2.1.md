DOCUMENTO CONTRACTUAL C1–C7 — FRONTERAS DEL SISTEMA PMSM
V2.1 — Revisión controlada posterior al cierre de D-06 y D-08, con cierre posterior de theta_m registrado en el repositorio
Proyecto: Digital Twin PMSM Siemens 1FT7087 — Plataforma de Control Híbrido Fecha: 2026-10-04 Estado: ESPECIFICACIÓN DOCUMENTAL VIGENTE; incorpora los cierres contractuales D-06 y D-08, y el cierre de theta_m registrado posteriormente en el repositorio mediante un commit identificado como D-09. El D-09 contractual de V2.0, correspondiente a la ubicación de VDC, permanece abierto. No contiene código, pseudocódigo, clases, validadores ni definiciones de bus ejecutables. Relación con V1.0: sustituye íntegramente a V1.0. No es un conjunto de parches (ver Anexo A). Criterio de prioridad: TRAZABILIDAD > COHERENCIA > SIMPLICIDAD > COMPLETITUD APARENTE. Regla absoluta: [TBD] y [CONFLICTING] son cierres prohibidos. Nada de este documento autoriza implementación.

0. CONTROL DOCUMENTAL
0.1 Leyenda de clasificación
Etiqueta	Significado
[HECHO]	Verificado directamente en los archivos adjuntos a esta revisión, o instrucción explícita del responsable del proyecto.
[CONF]	Valor o estado marcado CONFIRMED en la fuente primaria (Hard Data / parameters.py). Confirmado como dato de configuración no equivale a límite ni a requisito contractual.
[OBS]	Comportamiento observado en el código activo (PMSMBase, FOC B1.3, desacoplamiento B1.2, experimentos B1.x/B2.x).
[HIST]	Procede de documentación o implementaciones anteriores (M6/CloudE, skeleton.slx, Manifiesto ESDF v1.0, documentos conceptuales). Evidencia de procedencia; no contrato vigente.
[PROP]	Propuesta arquitectónica o de diseño. No es requisito.
[TBD]	Pendiente de decisión o de evidencia. Prohibido inferir; prohibido implementar.
[CONFLICTING]	Fuentes incompatibles. Se conservan ambas evidencias; no se resuelve.
Nota de cambio de leyenda: en V1.0 la etiqueta [CONF] significaba "contradicción". En V2.0 [CONF] significa "CONFIRMED en fuente primaria" y la contradicción se escribe [CONFLICTING].

0.2 Calificador "(decl.)"
(decl.) indica que la afirmación proviene del contexto consolidado declarado por el responsable del proyecto (F12) o de V1.0 (F1), pero la fuente primaria no está adjunta a esta revisión. Ejemplo: [OBS](decl.) = observado en el código activo según el responsable, sin que el archivo esté disponible aquí.

0.3 Base de evidencia de esta revisión
ID	Archivo	Naturaleza	Nota
F1	04_Fronteras_del__sistema.md	Documento V1.0 a reconstruir	Fuente de segunda mano para lo no adjunto
F2	Hard_Data	"M4 — HARD DATA" (datos recuperados de pmsm_1FT7087_M4_PLANT_BASELINE.slx)	Identificado por título; F1 y F8 lo citan como 01_M4_HARD_DATA.md
F3	03_documento_contraactual	Instrucciones de la tarea contractual previa (formato C1–C7, lista D-01…D-10)	Define el significado de D-03 y D-07
F4	paradigma_hibrido	Documento conceptual genérico sobre control híbrido neuro-difuso + MPC en "sistemas orgánicos"	No es específico del PMSM; contiene afirmaciones comerciales no contractuales
F5	MPC	Extracto conceptual MPC / ANFIS / TinyML	Subconjunto de F4 más notación matemática genérica
F6	skeleton.slx	Modelo Simulink histórico, inspeccionado a nivel XML (topología, constantes, código MATLAB embebido de los charts electrical_core, foc_core, pmsm_model)	[HIST]
F7	pmsm_base.py	Planta PMSMBase (M4_BASE)	[OBS]
F8	parameters.py	Parámetros M4 con trazabilidad	[CONF]/[OBS]
F9	foc.py	FOC reconstruido del M6/CloudE (interfaz con omega_ref, vdc; salida vd, vq)	[HIST]
F10	current_controller.py	PI de corriente "reconstruido a partir del M6"	[HIST]
F11	decoupling.py	Desacoplamiento "reconstruido a partir del M6"	[HIST]; identidad respecto de B1.2: [TBD]
F12	Mensaje de instrucciones V2.0	Contexto consolidado declarado por el responsable	Fuente de (decl.)
F13	Cierres contractuales D-06/D-08 y cierre posterior de theta_m registrado con identificador de commit D-09	Decisiones cerradas después de V2.0; commits y pruebas del repositorio	Base de esta revisión V2.1
0.4 Limitaciones de evidencia (leer antes de usar este documento)
No están adjuntos: la fuente del FOC B1.3; la fuente del desacoplamiento B1.2 (el decoupling.py adjunto se autodescribe como reconstrucción del M6/CloudE, por lo que no puede afirmarse que sea B1.2); los scripts y resultados de B1.4, B1.5, B1.6 y B2.x; transforms/park.py y transforms/clarke.py; "Notas importantes"; 01_construir_esqueleto; 02_CONTEXTO CONSOLIDADO; 05_CLOUDE_FORENSIC_REFERENCE; 06_KIMI_BUILD_RULES; Manifiesto ESDF v1.0.
Consecuencia: lo que este documento afirma sobre B1.3 y sobre experimentos es [OBS](decl.). Lo que afirma del Manifiesto es [HIST] por segunda mano (vía F1).
omega_m: D-06 queda CERRADO en V2.1 con base en la evidencia directa del código activo y de los consumidores del FOC. omega_m es velocidad angular mecánica de la planta, en rad/s; PMSMBase es productor y propietario; PlantOutput.omega_m la publica al FOC. No se introduce sensor ni estimador en la arquitectura contractual actual. omega_e = p·omega_m es una magnitud derivada localmente por el módulo que la necesita.
Ninguna evidencia ausente se completó por inferencia.
1. PROPÓSITO Y ALCANCE
Propósito. Formalizar, antes de cualquier implementación de contratos, las fronteras entre capas del sistema, separando estrictamente: señales de frontera, entradas externas, perturbaciones, parámetros de ejecución, parámetros de planta, parámetros de controlador, estados internos, datos históricos y decisiones abiertas.

Alcance. Cuatro fronteras:

Frontera	Capas	Estado
C-01	Planta ↔ FOC	Única con implementación funcional comprobada
C-02	FOC ↔ MPC	Futura — esqueleto
C-03	MPC ↔ ANFIS	Futura — esqueleto
C-04	ANFIS ↔ TinyML	Futura — esqueleto
Fuera de alcance: código de contratos, contracts.py, validadores, clases, buses ejecutables, resolución de D-01…D-10, modificación de omega_m o de cualquier archivo del proyecto.

Secuencia del proyecto: arquitectura → contratos → decisiones → interfaces → implementación. Este documento pertenece a la etapa "contratos".

2. ARQUITECTURA OBJETIVO
PLANTA / DIGITAL TWIN  ──C-01──  FOC  ──C-02──  MPC  ──C-03──  ANFIS  ──C-04──  TinyML
Capa	Interpretación	Estado de la afirmación
Planta / Digital Twin	Objeto físico-digital principal (Siemens 1FT7087; implementación activa PMSMBase)	[HECHO]
FOC	Capa de control actualmente funcional	[HECHO]
MPC	Capa futura	[PROP]
ANFIS	Capa futura de inteligencia/adaptación	[PROP]
TinyML	Posible tecnología futura de despliegue de la inteligencia (no se asume controlador independiente)	[PROP]
Advertencia de lectura. Las flechas indican el orden de capas desde lo físico hacia lo inteligente. No fijan el sentido de ningún flujo de señales (en particular, no establecen quién entrega referencias a quién entre FOC y MPC). Cada sentido de flujo debe decidirse en su contrato. [TBD]

Nota sobre componentes presentes en documentación histórica pero ausentes de la cadena objetivo. La lógica difusa (FIS) aparece como "supervisor" en F4/F5 y como FIS_Supervisor en skeleton.slx (F6, M7). No pertenece a la cadena Planta→FOC→MPC→ANFIS→TinyML ni tiene frontera contractual en este documento. Su ubicación arquitectónica es [TBD] (ver A-07).

3. ESTADO ACTUAL DE IMPLEMENTACIÓN
Elemento	Estado	Evidencia	Clasificación
Planta PMSMBase (M4_BASE)	Implementada. Estados id, iq, omega_m, theta_m; Euler explícito; sin VDC, sin B, sin Tfric en el balance	F7, F8	[OBS]
FOC B1.3	Implementado y usado en ensayos. Interfaz foc.step(ia, ib, ic, theta_m, omega_m, id_ref, iq_ref, dt) → va, vb, vc. Estructura: Clarke → Park → PI de corriente dq → desacoplamiento (B1.2) → Park inversa → Clarke inversa	F12, F1	OBS — fuente no adjunta
FOC histórico M6/CloudE	Reconstrucción adjunta. Interfaz omega_ref, omega_m, id, iq, vdc, dt → vd, vq, id_ref, iq_ref. Incluye PI de velocidad, PI de corriente, desacoplamiento, límite de iq, límite de tensión, anti-windup	F9, F10, F11; equivalente embebido en F6 (foc_core)	[HIST]
MPC	No implementado. En skeleton.slx existe solo PLACEHOLDER_MPC dentro de M6_Control	F6	[HECHO] no implementado / [HIST] placeholder
ANFIS	No implementado. En skeleton.slx existen PLACEHOLDER_ANFIS (M6) y el subsistema ANFIS_Adaptativo de M7, que entrega Kp_adapt/Ki_adapt a partir de constantes	F6	[HECHO] no implementado / [HIST]
TinyML	No implementado; no hay nodo asociado en los módulos M1–M7 de skeleton.slx	F6	[HECHO]
Experimentos B1.4, B1.5, B1.6, B2.x	Citados como evidencia de comportamiento; scripts y resultados no adjuntos	F1, F12	OBS
Estado real resumido [HECHO]: la base funcional comprobada es Planta + FOC. MPC, ANFIS y TinyML son arquitectura futura sin evidencia contractual.

4. DEFINICIÓN FORMAL DE FRONTERA CONTRACTUAL
4.1 Criterios
Un elemento es señal de frontera de un contrato C-0n si y solo si cumple todos estos criterios:

Es una magnitud física o funcional intercambiada en tiempo de ejecución entre las dos capas que el contrato nombra.
Tiene un productor y un consumidor que pertenecen a capas distintas de las dos que el contrato une.
Su dirección queda determinada por esas dos capas (Capa A → Capa B o Capa B → Capa A).
No es parámetro de configuración, perturbación del entorno, parámetro de ejecución, estado interno ni dato histórico.
Regla de exclusión explícita: que una variable aparezca como argumento o retorno de una función Python no la convierte en señal de frontera.

4.2 Taxonomía obligatoria de elementos
Categoría	Definición	¿Puede ser señal de frontera?	Dónde se documenta
Señal de frontera	Cumple 4.1	Sí	Sección del contrato correspondiente
Referencia / entrada de control	Valor objetivo entregado a una capa de control; su autoridad puede ser externa a las dos capas del contrato	Solo si una decisión documentada la eleva a frontera	Sección 5
Perturbación / entrada externa	Aplicada por el entorno de simulación o ensayo	No	Sección 5
Parámetro de ejecución	Condiciona cómo se ejecuta o integra (p. ej. paso temporal)	No	C3 (temporalidad) y sección 5
Parámetro de planta	Característica física del Digital Twin	No	Sección 6.12
Parámetro de controlador	Ganancia, límite o periodo propio del controlador	No	Sección 6.13
Estado interno	Estado dinámico propiedad de un módulo	No (salvo elevación documentada)	Sección 16
Dato histórico	Valor o estructura de implementaciones/documentos previos	No	Sección 21 y notas [HIST]
Decisión abierta	Cuestión sin resolver	No aplica	Secciones 17, 18 y 22
5. ENTRADAS EXTERNAS / PERTURBACIONES / PARÁMETROS DE EJECUCIÓN / ELEMENTOS QUE NO SON SEÑALES DE FRONTERA
Esta sección existe para impedir que V1.0 vuelva a mezclar categorías. Ningún elemento de esta tabla pertenece a C-01.

ID	Elemento	Categoría	Por qué NO es señal de C-01	Evidencia	Estado	Relación
NB-01	id_ref	Referencia / entrada de control	Es entrada del FOC B1.3; su productor, propietario y autoridad no están determinados. No es señal Planta↔FOC	F12; F1 (B1.4 usa constantes en el harness); F9 y F6 foc_core (en el histórico es salida del FOC, con id_ref = 0 fijo); F6 raíz (constante id_ref_const = 0 hacia REF_BUS)	OBS / [HIST] / [CONFLICTING]	D-04, D-02
NB-02	iq_ref	Referencia / entrada de control	Ídem NB-01	F12; F1 (B1.4: iq_ref = 10); F9/F6 (histórico: salida del PI de velocidad, limitada a ±112.43 A); F6 raíz (iq_ref_const = 0)	OBS / [HIST] / [CONFLICTING]	D-04, D-02
NB-03	t_load	Perturbación / entrada externa a la planta	Lo aplica el entorno de simulación o ensayo sobre la planta; no la produce el FOC ni la consume el FOC	F7 (PlantInput.t_load, "torque de carga total"); F1 (harness de ensayo); F6 (bloque Tl_step en M4_PhysicalPlant)	[OBS] / [HIST]	—
NB-04	dt	Parámetro de ejecución / integración	No es magnitud física intercambiada; condiciona la ejecución de ambos módulos	F7 (step(inp, dt)); F12	[OBS]	D-08; se documenta en C3
NB-05	id, iq (en PlantOutput)	Estado interno de la planta expuesto como observable	El FOC B1.3 consume ia, ib, ic y transforma internamente; id/iq de la planta no cruzan hacia el FOC en el lazo activo	F7; F12; F1	OBS	Sección 16
NB-06	te (en PlantOutput)	Magnitud calculada de la planta, observable	No es consumida por el FOC; ecuación de Te es de referencia, no verificada como ley interna de Simscape M4	F7 (docstring y electromagnetic_torque)	[OBS]	Sección 16
NB-07	omega_ref	Referencia de velocidad	No existe en la interfaz de B1.3; sí en el FOC histórico y en REF_BUS de skeleton.slx (omega_ref_const = motor.omega_nominal)	F9, F6, F12	[HIST]	D-02, D-05
NB-08	VDC / vdc	Parámetro/entrada de tensión de bus	No pertenece actualmente a la parametrización activa de la planta; no es argumento de B1.3 (decl.). Existe en el FOC histórico y en el modelo Simulink histórico	F12; F7/F8 (ausente); F9; F6 (VDC_const = motor.VDC en M4, VDC en M3 y M6)	[HECHO] ausencia en planta activa / [HIST]	D-09
NB-09	vd, vq	Salida del FOC histórico / variables internas dq	No son la salida de B1.3	F9; F6	[HIST]	D-01
NB-10	DUTY_A/B/C, GATE_*, ENABLE, FAULT	Señales del módulo histórico M3 (interfaz eléctrica)	No existen en C-01 activo	F6 (electrical_core)	[HIST]	D-01, D-09
NB-11	omega_e, theta_e	Magnitudes derivadas (p × mecánica)	Derivadas internamente por cada módulo que las necesita	F7 (theta_e, omega_e); F9; F6	[OBS] / [HIST]	D-06
NB-12	modo_operacion	Entrada de REF_BUS histórico	Aparece como constante en la raíz de skeleton.slx; sin evidencia de uso en el FOC activo	F6	[HIST]	—
NB-13	Parámetros de planta (Rs, Ld, Lq, λm, p, J, …)	Parámetro de planta	Son configuración del Digital Twin, no señales	F8, F2	[CONF]	Sección 6.12
NB-14	Parámetros del FOC (kp/ki, límites, ts_*, λm de control)	Parámetro de controlador	Son configuración del controlador, no de la planta ni señales	F9, F10, F6	[HIST] (B1.3: [TBD])	Sección 6.13
NB-15	Integradores PI, contador de sub-muestreo, _iq_ref retenido	Estado interno del FOC	No cruzan frontera	F9, F10	[HIST]	Sección 16
NB-16	Buses históricos (PLANTA_BUS, GATE_BUS, STATE_BUS, REF_BUS, CONTROL_BUS, ADAPT_BUS, SAFETY_BUS; TINY_BUS y DIAG_BUS citados por F1)	Dato histórico	No son contratos actuales. Los siete primeros están en F6; TINY_BUS, DIAG_BUS y el nodo M8 se conocen solo por F1 (Manifiesto, no adjunto)	F6, F1	[HIST]	D-08
NB-17	PlantInput.theta_m (entrada de la planta)	Entrada observada de la planta con productor no determinado	No es señal FOC→Planta según la definición de C-01; es parte del problema de ownership de theta_m	F7	[OBS] / [TBD]	A-02, D-06
6. C-01 — PLANTA ↔ FOC
6.1 Alcance y separación obligatoria A / B
Alcance de C-01 (decisión de alcance del responsable para V2.0 [HECHO]): C-01 es exclusivamente la frontera física Planta ↔ FOC.

Dirección	Señales
Planta → FOC	ia, ib, ic, theta_m, omega_m
FOC → Planta	va, vb, vc
Esta lista fija el alcance de la interfaz activa observada. No equivale a cerrar D-01 (frontera eléctrica definitiva). D-06 (omega_m) ya está cerrado en esta revisión.

A. Interfaz observada actualmente (qué existe en código/experimentos):

Planta: PMSMBase.step(PlantInput(va, vb, vc, t_load, theta_m), dt) → PlantOutput(ia, ib, ic, id, iq, omega_m, theta_m, te) — [OBS] (F7).
FOC activo B1.3: foc.step(ia, ib, ic, theta_m, omega_m, id_ref, iq_ref, dt) → va, vb, vc — OBS (F12, F1).
De esas interfaces solo las ocho señales de la tabla anterior son señales de C-01. El resto de argumentos (id_ref, iq_ref, t_load, dt) y de campos de salida (id, iq, te) se tratan en la sección 5.

B. Contrato arquitectónico objetivo: lo que debería formalizarse tras resolver las decisiones pendientes (sección 22). Hoy es [TBD] en todo lo que no coincide con A.

6.2 C-01 / C1 — Semántica
ID	Señal	Categoría	Significado	Dirección	Productor	Consumidor	Propósito	Evidencia	Estado
C01-01	ia	Señal (corriente de fase)	Corriente de la fase a	Planta → FOC	PMSMBase	FOC B1.3	Realimentación de corriente (el FOC transforma internamente)	F7 PlantOutput.ia; F12	[OBS]
C01-02	ib	Señal (corriente de fase)	Corriente de la fase b	Planta → FOC	PMSMBase	FOC B1.3	Ídem	F7; F12	[OBS]
C01-03	ic	Señal (corriente de fase)	Corriente de la fase c	Planta → FOC	PMSMBase	FOC B1.3	Ídem	F7; F12	[OBS]
C01-04	theta_m	Estado mecánico publicado	Posición mecánica del rotor; theta_e = p · theta_m con p = 4	Planta → FOC	PMSMBase	FOC B1.3	Ángulo para Park	F7; evidencia D-06 / A-02	[OBS] / CLOSED D-06 / A-02
C01-05	omega_m	Estado mecánico publicado	Velocidad angular mecánica del rotor, en rad/s	Planta → FOC	PMSMBase	FOC B1.3	Uso por el FOC / controlador de velocidad	F7; evidencia D-06	[OBS] / CLOSED D-06
C01-06	va	Comando (tensión de fase)	Tensión aplicada a la fase a	FOC → Planta	FOC B1.3	PMSMBase	Actuación eléctrica	F7 PlantInput.va; F12	OBS
C01-07	vb	Comando (tensión de fase)	Tensión aplicada a la fase b	FOC → Planta	FOC B1.3	PMSMBase	Ídem	F7; F12	OBS
C01-08	vc	Comando (tensión de fase)	Tensión aplicada a la fase c	FOC → Planta	FOC B1.3	PMSMBase	Ídem	F7; F12	OBS
Nota de tipos. En el Digital Twin una "medición" puede ser el estado real de la planta o una medición con modelo de sensor. En el código observado la planta publica directamente sus estados; no hay modelo de sensor entre ambos módulos [OBS] (en skeleton.slx el módulo M1_Instrumentacion es un paso directo sin lógica [HIST]). Si el contrato futuro debe incluir ruido, retardo o cuantización de medición: [TBD].

6.3 omega_m — caso contractual especial (D-06)

Estado contractual: CERRADO.

D-06 establece la semántica y ownership de omega_m sin introducir un sensor o estimador que no forme parte de la arquitectura actualmente implementada.

Aspecto	Contenido	Estado
Significado	Velocidad angular mecánica del rotor de la PMSM	CERRADO
Unidad	rad/s	CERRADO
Referencia	Eje mecánico del rotor; signo positivo asociado al sentido de incremento de theta_m	CERRADO
Productor	PMSMBase / PlantOutput.omega_m	CERRADO
Propietario	Planta PMSMBase	CERRADO
Consumidor	FOC / controlador de velocidad; otros consumidores solo si se documentan posteriormente	CERRADO
Dirección	Planta → FOC	CERRADO
Relación eléctrica	omega_e = p · omega_m; omega_e es magnitud derivada, no una señal adicional de C-01	CERRADO
Modificación por FOC	El FOC consume omega_m; no puede modificar el estado de la planta	CERRADO
Temporalidad	Se publica como parte de PlantOutput en cada paso ejecutado por la planta; las frecuencias contractuales de ejecución siguen perteneciendo a D-08/C3	CERRADO para ownership y semántica; temporalidad de ejecución separada
Sensor / estimador	No existe ni se introduce modelo de sensor/estimador en el contrato actual	CERRADO
Presentación	RPM puede utilizarse para reporte/presentación; la unidad interna contractual es rad/s	CERRADO

Evidencia directa de cierre:
- PMSMBase mantiene omega_m como estado mecánico y lo publica mediante PlantOutput.omega_m.
- El FOC/controlador de velocidad consume omega_m como velocidad mecánica en rad/s.
- El FOC reconstruido deriva omega_e = p · omega_m cuando necesita la velocidad eléctrica.
- Los ensayos B2.x utilizan output.omega_m como medición de velocidad.
- No existe evidencia contractual que requiera un sensor o estimador entre PMSMBase y FOC.

Regla arquitectónica resultante:

M4 / Planta
    │
    ├── omega_m [rad/s]
    └── theta_m [rad]
             │
             ▼
         M3 / FOC
             ├── usa omega_m en el lazo de velocidad
             └── deriva omega_e = p·omega_m cuando corresponde

No se introduce una capa de sensado/estimación para cerrar D-06.

6.4 theta_m — ownership contractual (D-06 / A-02)

Estado contractual: CERRADO.

El cierre de D-06 / A-02 establece que theta_m pertenece a la planta. La planta conserva el estado interno, lo integra y lo publica mediante PlantOutput. theta_m no pertenece a PlantInput. El cierre fue registrado posteriormente en el repositorio mediante un commit identificado como D-09; este identificador no sustituye el significado contractual de D-09 en V2.0, que corresponde a la ubicación de VDC.

Aspecto	Contenido	Estado
Estado interno	self._theta_m es estado propio de PMSMBase	CERRADO
Evolución	d(theta_m)/dt = omega_m	CERRADO
Productor	PMSMBase	CERRADO
Propietario	Planta PMSMBase	CERRADO
Salida	PlantOutput.theta_m	CERRADO
Entrada PlantInput.theta_m	Eliminada del contrato activo; no se acepta como mecanismo para sobrescribir el estado de la planta	CERRADO
Consumidor	FOC B1.3, para Park y demás usos autorizados por C-01	CERRADO
Relación eléctrica	theta_e = p · theta_m	CERRADO
Modificación por FOC	El FOC consume theta_m; no puede modificar el estado de la planta	CERRADO

El cierre de D-06 / A-02 elimina el doble rol observado en V2.0. La evidencia histórica de que existió PlantInput.theta_m se conserva en V2.0 y en los artefactos históricos; no se borra ni se reescribe como si nunca hubiera existido.

La salida PlantOutput.theta_m pertenece al snapshot coherente definido por D-08.

6.5 Frontera eléctrica y D-01
Tres representaciones coexisten en la evidencia. No se elige ninguna.

Variante	Forma	Dónde aparece	Estado
A	(va, vb, vc) — salida del FOC B1.3 y entrada de PlantInput	F7 (PlantInput); F12	[OBS] / OBS
B	(vd, vq) — salida del FOC reconstruido M6	F9; F6 foc_core	[HIST]
C	DUTY_A/B/C normalizados + VDC_in — entrada de la planta en el modelo Simulink histórico; el cálculo Va = (DUTY − 0.5) · VDC_in está dentro de pmsm_model	F6 (electrical_core produce duty desde Vd_in, Vq_in; pmsm_model los consume)	[HIST]
En skeleton.slx la conversión (vd,vq)→(va,vb,vc)→duty ocurre en M3 con normalización por VDC; es decir, las tensiones de fase existen allí como magnitud intermedia interna de M3, no como frontera.

Estado: [CONFLICTING] / DECISIÓN PENDIENTE (D-01). C-01 en este documento usa la variante A solo porque es la interfaz activa observada y el alcance fijado por el responsable.

6.6 C-01 / C2 — Física
Señal	Unidad	Sistema de referencia	Signo	Rango	Resolución	Valor nominal
ia, ib, ic	A	Fases abc del devanado (estrella, neutro no expuesto [CONF] F2 §1). Convención Park de la planta: QleadsD_AphaseToDaxis [CONF]	Convención de signo de corriente (motor/generador): [TBD]	No documentado	[TBD]	id/iq nominal 53 A [CONF]; no documentado si es pico, RMS u otra base (V1.0 afirmó "RMS" sin respaldo en F2)
theta_m	rad	Mecánico; origen: angular_position inicial 0 deg [CONF]; relación theta_e = p·theta_m [OBS] y "relación habitual" [CONF] F2 §21 con verificación de convención pendiente	Creciente con giro positivo [OBS]	No acotado en el código observado	[TBD]	No aplica (F2 lista angular_position_nominal_value = 1 deg como valor de configuración, no como condición de escenario)
omega_m	rad/s	Velocidad angular mecánica del rotor de la PMSM; propietario: planta PMSMBase	Positivo = sentido de incremento de theta_m [OBS]	No documentado	[CERRADO D-06]	471.24 rpm [CONF] F2 — ver D-05 y A-04
va, vb, vc	V	Fase respecto a neutro no verificado (el código aplica Clarke asumiendo suma cero) [TBD]	Bipolar [OBS]	No documentado en B1.3; límite de tensión histórico: ver 6.10	[TBD]	Sin dato
Valores nominales de F2 §5 (id, iq = 53 A; torque 46 N·m; velocidad 471.24 rpm; posición 1 deg): son "valores nominales/configurados del modelo". F2 indica expresamente que no deben interpretarse como condiciones de cada escenario. Aquí tampoco son rangos ni límites.

6.7 C-01 / C3 — Temporal
dt no es señal física; se documenta aquí como parámetro de ejecución (NB-04).

Aspecto	Contenido	Clasificación
Paso de ejecución observado	dt = 50 µs en B1.4 y B2.x según V1.0	OBS
Frecuencia equivalente	1/dt = 20 kHz. Es frecuencia observada de ejecución, no una frecuencia contractual universal	OBS — D-08 cerrado como semántica de snapshot; la frecuencia contractual por módulo permanece separada
Otras apariciones de 50 µs	ts_current = 50e-6 por defecto en foc.py; Ts_c y Ts en los charts de skeleton.slx; "Ts = 50e-6 s" en el bloque CloudE de F2 §22	[HIST]
Implicación	El valor 50 µs no discrimina entre "observado en Python actual" y "heredado de CloudE"; por eso no se congela	A-08
Frecuencias históricas	20 kHz / 5 kHz / 1 kHz / 100 Hz (Manifiesto, vía F1); en F6: RT_Speed = 200 µs y RT_Supervisor = 1 ms; ts_speed = 200 µs en F9	HISTÓRICA — NO CONGELADA
Lazo de velocidad	No existe en la interfaz de B1.3; en el histórico se ejecuta cada 200 µs	OBS / [HIST] — D-02
Sincronización	Secuencial por pasos con el mismo dt entre FOC y planta; jitter no documentado	OBS
Orden de actualización dentro de PMSMBase.step	(1) cálculo con estados de inicio; (2) integración Euler explícita de id, iq, omega_m, theta_m; (3) reconstrucción de corrientes abc y demás campos de salida usando el estado post-integración, de acuerdo con el snapshot coherente de D-08	[OBS] / CLOSED D-08
¿El FOC usa salidas del mismo paso o del anterior? (latencia lazo)	No determinable sin la fuente del harness	[TBD]
Inicialización de la planta	id = iq = 0, omega = 0, theta = 0 — "CONFIRMED AS CONFIGURATION" (specify off)	[CONF] / [OBS]
Inicialización del FOC B1.3	[TBD] (fuente no adjunta). En el histórico adjunto los integradores parten en 0	[TBD] / [HIST]
Comportamiento ante dato antiguo (stale)	Sin mecanismo definido	[TBD]
Método de integración	Euler explícito, declarado como "PROPOSED" en F7	[PROP]
6.8 C-01 / C4 — Ownership y autoridad
Se distingue propiedad del dato de autoridad para actuar.

Elemento	Productor	Propietario del dato	Quién puede modificar	Consumidor	Autoridad sobre el sistema	Estado
ia, ib, ic	PMSMBase	PMSMBase (Planta)	Solo la dinámica de la planta	FOC B1.3	El FOC no modifica estos datos	[OBS]
theta_m	PMSMBase (salida)	Planta PMSMBase	La planta PMSMBase	FOC B1.3	El FOC consume; no modifica	[OBS] / CLOSED D-06 / A-02
omega_m	PMSMBase / PlantOutput.omega_m	Planta PMSMBase	La planta PMSMBase	FOC B1.3	Rad/s; el FOC no modifica	CLOSED D-06
va, vb, vc	FOC B1.3	FOC	FOC	PMSMBase	El FOC es el único productor observado del comando de tensión	OBS
Autoridad sobre referencias de corriente y de velocidad: fuera de C-01; ver NB-01, NB-02, NB-07 y D-02/D-04. Debe existir un único propietario lógico por estado. Para C-01, theta_m y omega_m tienen propietario cerrado en la planta por D-06 / A-02. id_ref e iq_ref permanecen fuera de este cierre y siguen sujetos a D-02 / D-04.

6.9 C-01 / C5 — Validez
Estado: NO IMPLEMENTADO — CONTRATO PROPUESTO. No existe en el código activo ningún validador ni estado de validez de señales OBS. Lo único existente son validaciones de software: dt <= 0 lanza error en step, y PMSMParameters.validate() comprueba coherencia de parámetros (por ejemplo n_pole_pairs == 4); ninguna es validez de señal.

Los estados candidatos (VALID, INVALID, UNAVAILABLE, INITIALIZING, STALE, OUT_OF_RANGE) se listan en la matriz de la sección 14 con su justificación de evidencia. No se definen criterios, umbrales ni enumeraciones.

6.10 C-01 / C6 — Seguridad
Se distingue límite físico / del controlador / experimental / histórico-documental. Ninguno se convierte en otro.

Tipo	Contenido	Estado
Límite físico de la planta	Ninguno confirmado como límite. Los valores nominales de F2 §5 no son límites; los rangos de tabulación (±200 A en mapas Ld/Lq, ±2 A en iVec) son rangos de tablas, no de operación	[TBD]
Límite del controlador (activo B1.3)	Según V1.0 no hay límite de corriente ni de tensión implementado en B1.3; fuente no adjunta	OBS — verificación pendiente
Límite del controlador (histórico M6)	iq limitada a ±112.43 A; v_max = max(1, VDC)/√3 · 0.95; anti-windup por rollback (F9, F10, F6)	[HIST] — no confirmado como límite contractual
Límite experimental	Ninguno documentado en los archivos adjuntos (los valores de referencia de ensayos, p. ej. iq_ref = 10 en B1.4, son condiciones de ensayo, no límites)	[TBD]
Límite histórico/documental	"límite de convertidor 141 A", "VDC = 565 V", ">3100 rpm debilitamiento" (citados por V1.0 desde el Manifiesto; no adjunto)	[HIST] por segunda mano
Saturación	Sin mecanismo activo observado en B1.3 (decl.). En skeleton.slx M3 satura duty a [0,1]; limites_activos = [false,false,false,false] fijo; FAULT = false fijo	OBS / [HIST]
Fallback / condición de fallo / estado seguro / autoridad de protección	No definidos	[TBD]
Prohibido importar mecanismos históricos (anti-windup, límite de tensión, límite de iq) como si fueran vigentes.

6.11 C-01 / C7 — Trazabilidad
Afirmación	Fuente	Ubicación	Experimento	Evidencia/estado
Interfaz de planta PlantInput/PlantOutput	F7	Cabecera y clases	B1.x	[OBS]
Interfaz FOC B1.3	F12, F1	Instrucciones / C-01 de V1.0	B1.4–B2.x	OBS
theta_e = p · theta_m	F7	propiedad theta_e, step	B1.x	[OBS]
Doble rol theta_m (entrada y estado)	F7	step: self._theta_m = inp.theta_m	—	[OBS]
theta_m como estado propio en el histórico	F6	chart pmsm_model (theta_mem)	—	[HIST]
Situación de parche en omega_m	F12, F1 ("Notas importantes")	—	B2.x (según F1)	OBS / [CONFLICTING]
Interfaz FOC histórica	F9; F6 foc_core	step / chart	—	[HIST]
Tres variantes de frontera eléctrica	F7, F9, F6	ver 6.5	—	[CONFLICTING]
Parámetros M4	F2, F8	F2 §2–§5, §24; parameters.py	—	[CONF]
Paso 50 µs en ensayos	F1	C-01/C3 de V1.0	B1.4, B2.x	OBS
6.12 Parámetros de planta (referencia M4_BASE)
Son parámetros de la planta, no señales ni parámetros del controlador. Fuente única: F2; implementación: F8.

Parámetro	Valor	Unidad	Estado	Nota
Rs	0.05	Ω	[CONF]	
Ms	0.00002	H	[CONF]	No consumido por la dinámica de pmsm_base.py
L0	0.00016	H	[CONF]	No consumido por la dinámica de pmsm_base.py
Ld	0.0012	H	[CONF]	
Lq	0.0012	H	[CONF]	Ld = Lq en los valores recuperados
λm (lambda_m)	0.107245	Wb (F8, instrucciones) / N·m·s/rad (F2 §3, §24)	Valor [CONF]; procedencia PENDING VERIFICATION	No sustituir por 0.1100 (CloudE). Etiqueta de unidad en conflicto: A-01
N	6	—	[CONF]	Parámetro del bloque; no es número de pares de polos; no consumido por la dinámica
n_pole_pairs (p)	4	—	[CONF]	8 polos físicos
J	0.00416	kg·m²	[CONF]	
id nominal / iq nominal	53 / 53	A	[CONF] como configuración	Base (pico/RMS) no documentada
Torque nominal	46	N·m	[CONF] como configuración	Ver A-05
Velocidad nominal	471.24	rpm (según F2)	[CONF] como configuración	D-05 / A-04
Posición angular nominal	1	deg	[CONF] como configuración	
Condiciones iniciales	id = iq = 0; torque = 0; velocidad = 0; posición = 0	A, N·m, rpm, deg	[CONF] como configuración	specify off
Convención de Park	QleadsD_AphaseToDaxis	—	[CONF]	Debe conservarse
Devanado / neutro	wye / expose_neutral_port = no	—	[CONF]	
Interpolación / pérdidas	linear / loss_param = none	—	[CONF]	No introducir pérdidas sin fuente
Parámetros térmicos	alpha 3.93e-3 1/K; alpha_flux −0.001 1/K; Tmeas 298.15 K; masas térmicas 100 y 200 J/K	—	[CONF] como almacenados	La dinámica térmica no está implementada
B (fricción viscosa)	—	N·m·s/rad	PENDING	No usar 0.001 de CloudE
Tfric	—	N·m	PENDING	No usar 0.5 de CloudE
Procedencia de λm	—	—	PENDING	
VDC	—	V	No pertenece a la parametrización activa de la planta	D-09
Mapas recuperados (Ld/Lq, PmMatrix, dflux, Torque, dq0, IBX, pérdidas de rotor)	varios	varios	Recuperados; activación PENDING VERIFICATION	No usar automáticamente. PmMatrix = 0.1 no se asume igual a λm (D-10)
6.13 Parámetros del controlador (separados de la planta)
Son parámetros del FOC. Solo se dispone de los del FOC histórico/reconstruido; los de B1.3 son [TBD] (fuente no adjunta).

Parámetro	Valor en el FOC histórico	Fuente	Estado
Ganancias PI de corriente d/q	kp = 15.0796; ki = 628.3185	F10; F6 foc_core	[HIST]
Ganancias PI de velocidad	kp = 5.2804; ki = 1.2693	F9; F6 foc_core	[HIST]
Periodos	ts_current = 50e-6; ts_speed = 200e-6	F9; F6	[HIST] — D-08
Límite de iq	±112.43 A	F9; F6	[HIST] — no contractual
Límite de tensión	v_max = max(1, vdc)/√3 · 0.95	F9; F6	[HIST] — D-09
id_ref	0 fijo internamente	F9; F6	[HIST] — D-04
λm usado por el desacoplamiento	0.1100 (valor por defecto de foc.py y foc_core)	F9; F6	[HIST]; distinto de λm de planta 0.107245 (≈ 2.6 % de diferencia, aritmético). Valor usado en B1.2/B1.3: [TBD]
Ld, Lq, pares de polos del controlador	0.0012 H; 0.0012 H; 4	F9	[HIST]
Anti-windup	Rollback de la integral cuando se satura	F9; F10	[HIST]
Ganancias y límites de B1.3	—	—	[TBD]
6.14 FOC activo B1.3 frente a FOC histórico M6/CloudE (no mezclar)
Aspecto	FOC activo B1.3	FOC histórico M6/CloudE
Interfaz	(ia, ib, ic, theta_m, omega_m, id_ref, iq_ref, dt) → (va, vb, vc)	(omega_ref, omega_m, id, iq, vdc, dt) → (vd, vq, id_ref, iq_ref)
Estructura	Clarke → Park → PI de corriente dq → desacoplamiento B1.2 → Park inv. → Clarke inv.	PI de velocidad → PI de corriente dq → desacoplamiento → límite de tensión → anti-windup; transformadas abc↔dq fuera del FOC (M3 en el histórico)
Lazo de velocidad	No presente en la interfaz	Presente (kp = 5.2804, ki = 1.2693; cada 200 µs)
Origen de id_ref/iq_ref	Entrada del FOC	Salida del FOC (id_ref = 0; iq_ref del PI de velocidad)
Uso de vdc	No (decl.)	Sí (límite de tensión)
Límites	Ninguno implementado (decl.)	iq ±112.43 A; v_max con vdc
Evidencia	F12, F1; fuente no adjunta	F9, F10, F11, F6 (adjuntos)
Estado	OBS	[HIST]
Uso permitido del histórico: identificar conflictos y decisiones (D-01, D-02, D-04, D-05, D-08, D-09). No redefine automáticamente el contrato activo.

7. C-02 — FOC ↔ MPC (futuro — esqueleto)
Estado: MPC no está implementado [HECHO]. Este contrato fija la obligación de definirlo antes de implementarlo. No contiene señales.

7.1 C-02 / C1 — Semántica
Pregunta	Respuesta respaldada por evidencia	Estado
Rol conceptual del MPC	"Orquestador" que usa un modelo predictivo (que puede ser el propio ANFIS) para simular el futuro, resuelve una optimización con restricciones y aplica solo la primera acción (horizonte deslizante)	[HIST] (F4, F5)
Qué información podría recibir	Modelo predictivo y "directrices" del supervisor difuso (F5). Señales concretas procedentes del FOC: no documentadas	[HIST] / [TBD]
Qué podría producir	F5: "genera las señales de control efectivas para las múltiples variables". Qué magnitud concreta entrega a o a través del FOC: no documentado	[HIST] / [TBD]
Relación con el FOC	No decidida. Dos lecturas conviven en el material: MPC como capa que da órdenes al FOC (orden de capas de la arquitectura objetivo) y MPC como "ejecutor" que genera las señales de control (F5). En skeleton.slx, PLACEHOLDER_MPC está dentro de M6_Control, junto a FOC_CLASICO, sin contenido	[CONFLICTING] (D-07, A-06)
Qué NO debe controlar directamente	No decidido	[TBD]
Restricciones que podría considerar	"límites de actuadores, niveles de seguridad" (conceptual); notación genérica u_min/u_max, x_min/x_max sin mapeo a variables del PMSM	[HIST] — valores: [TBD]
Elementos matemáticos históricos	Función de costo con pesos Q y R, horizontes Hp y Hu; Q = FIS(e, ė), R = FIS(e, ė)	[HIST] — no se fijan algoritmo, horizonte, función de costo ni pesos
Señales concretas FOC→MPC y MPC→FOC: [TBD].

7.2 C-02 / C2 — Física
Unidades, referencias, signos, rangos: [TBD] en su totalidad (sin evidencia).

7.3 C-02 / C3 — Temporal
Frecuencia, periodo, sincronización, latencia: [TBD]. Las cifras históricas de buses (5 kHz ADAPT_BUS, 1 kHz SAFETY_BUS, según F1) y los 200 µs / 1 ms de RT_Speed/RT_Supervisor en F6 son HISTÓRICAS — NO CONGELADAS y no se atribuyen a MPC.

7.4 C-02 / C4 — Ownership y autoridad
Mientras C-02 no exista, la autoridad sobre id_ref/iq_ref permanece según D-04. Todo traspaso de autoridad a un MPC futuro requiere decisión explícita. Propietarios y autoridades: [TBD].

7.5 C-02 / C5 — Validez
No aplica hasta que existan señales. [TBD]

7.6 C-02 / C6 — Seguridad
Solo conceptual: el MPC "respeta restricciones del sistema" [HIST]. La política histórica de "fallback a FOC" (SAFETY_BUS, según F1) es [HIST] y no vinculante. Mecanismos concretos: [TBD].

7.7 C-02 / C7 — Trazabilidad
Afirmación	Fuente	Estado
MPC como orquestador/optimizador con restricciones y horizonte deslizante	F4, F5	[HIST]
Notación Q, R, Hp, Hu, u_min/u_max, x_min/x_max; ajuste de pesos por FIS	F5	[HIST]
MPC dentro de M6 como PLACEHOLDER_MPC	F6 (system_9)	[HIST]
MPC en la arquitectura objetivo	F12	[PROP]
Discrepancia documental sobre el rol de MPC	F1 ("Notas importantes", no adjunta)	[CONFLICTING] — D-07
8. C-03 — MPC ↔ ANFIS (futuro — esqueleto)
Estado: ni MPC ni ANFIS están implementados [HECHO].

8.1 C-03 / C1 — Semántica
Pregunta	Respuesta respaldada por evidencia	Estado
Rol de ANFIS en el material	Tres lecturas distintas: (a) modelo predictivo adaptable usado por el MPC (F4, F5); (b) controlador directo que aprende la ley de control a partir de datos de un MPC (F4); (c) adaptador de ganancias del FOC: en skeleton.slx el subsistema ANFIS_Adaptativo de M7 entrega Kp_adapt y Ki_adapt hacia M6 por ADAPT_BUS, con valores constantes 5.2804 y 1.2693	[HIST]; conflicto entre lecturas: A-06
Información que usaría ANFIS	Notación θ[k] = θ₀ + NN(e, ė, historial) y Q, R = FIS(e, ė) (genéricas)	[HIST] — entradas concretas: [TBD]
Parámetros que podría adaptar	Parámetros del modelo (θ) y pesos (Q, R) según F5; ganancias PI según F6	[HIST] — cuáles es contractual: [TBD]
Recomendaciones vs comandos vs límites	No definidos	[TBD]
Control directo de la planta	No se asume	[HECHO] criterio de esta V2.0
Reglas, funciones de pertenencia, entradas, salidas, formato del modelo	No se fijan	[TBD]
8.2 C-03 / C2 — Física
[TBD] en su totalidad.

8.3 C-03 / C3 — Temporal
[TBD]. La cifra histórica de 5 kHz (ADAPT_BUS, según F1) es HISTÓRICA — NO CONGELADA. F4/F5 indican entrenamiento offline "o con actualizaciones online muy suaves": descriptivo, sin periodo.

8.4 C-03 / C4 — Ownership y autoridad
[TBD]. Está abierto si el modelo predictivo es propiedad del ANFIS y lo consulta el MPC, o si el MPC lo internaliza; ambas lecturas aparecen en el material histórico y se conservan como ambigüedad.

8.5 C-03 / C5 — Validez
[TBD].

8.6 C-03 / C6 — Seguridad
Solo conceptual: actualizaciones online "muy suaves" [HIST]. En skeleton.slx existe un subsistema Guardian_Lyapunov en M7 con salida safety_mode constante 0 (y FIS_Supervisor con un default_mode constante) [HIST]. Mecanismos vigentes: [TBD].

8.7 C-03 / C7 — Trazabilidad
Afirmación	Fuente	Estado
ANFIS como modelo predictivo del MPC	F4, F5	[HIST]
ANFIS como controlador directo	F4	[HIST]
θ[k] = θ₀ + NN(e, ė, historial)	F5	[HIST]
Kp_adapt/Ki_adapt por ADAPT_BUS	F6 (system_root, system_9, system_69, system_82)	[HIST]
ANFIS como capa futura de inteligencia/adaptación	F12	[PROP]
Afirmaciones comerciales/de desempeño de F4 (ahorros, "10 veces más rápido", mercado)	F4	Excluidas: no son evidencia contractual
9. C-04 — ANFIS ↔ TinyML (futuro — esqueleto)
Estado: ni ANFIS ni TinyML están implementados [HECHO]. TinyML se trata como posible tecnología de despliegue de la inteligencia, no como controlador independiente.

9.1 C-04 / C1 — Semántica
Pregunta	Respuesta respaldada por evidencia	Estado
Rol	Despliegue compacto de un modelo entrenado en hardware de bajo consumo	[HIST] (F4, F5)
Modelo que podría desplegarse	"Red neuronal/ANFIS" entrenado offline (F5). Formato, cuantización, tamaño: no documentados	[HIST] / [TBD]
Entradas / salidas	No documentadas	[TBD]
Hardware	F4 menciona Raspberry Pi; F5 menciona esp32 y Raspberry Pi como lo "recomendable". Es recomendación conceptual, no requisito ni restricción	[HIST] — no se asume hardware
Memoria, latencia, frecuencia, métricas, mecanismo de actualización	No documentados	[TBD]
9.2 C-04 / C2 — Física
[TBD].

9.3 C-04 / C3 — Temporal
[TBD]. La cifra histórica de 1 kHz (TINY_BUS, según F1) es HISTÓRICA — NO CONGELADA.

9.4 C-04 / C4 — Ownership y autoridad
[TBD]. No se asume que TinyML tenga autoridad propia sobre variable alguna.

9.5 C-04 / C5 — Validez
[TBD]. La política histórica "ignorar predicción" (según F1) es [HIST] y no vinculante.

9.6 C-04 / C6 — Seguridad
Nada documentado. [TBD]

9.7 C-04 / C7 — Trazabilidad
Afirmación	Fuente	Estado
TinyML como despliegue en dispositivos de bajo consumo	F4, F5	[HIST]
TinyML como posible tecnología de despliegue	F12	[PROP]
No hay nodo TinyML en M1–M7 de skeleton.slx	F6	[HECHO]
10. C1–C7 POR FRONTERA (ÍNDICE)
Dimensión	C-01	C-02	C-03	C-04
C1 Semántica	6.2–6.5	7.1	8.1	9.1
C2 Física	6.6	7.2	8.2	9.2
C3 Temporal	6.7	7.3	8.3	9.3
C4 Autoridad	6.8	7.4	8.4	9.4
C5 Validez	6.9	7.5	8.5	9.5
C6 Seguridad	6.10	7.6	8.6	9.6
C7 Trazabilidad	6.11	7.7	8.7	9.7
11. MATRIZ MAESTRA DE SEÑALES
Solo C-01 contiene señales de frontera. Los elementos que no son frontera están en la sección 5.

ID	Señal	Contrato	Productor	Consumidor	Propietario	Unidad	Referencia	Signo	Rango	Temporalidad	Validez	Autoridad	Evidencia	Estado
C01-01	ia	C-01	PMSMBase	FOC B1.3	Planta	A	Fase a, devanado wye	[TBD]	[TBD]	Por paso de planta; periodo contractual [TBD]	NO IMPLEMENTADO	Planta (dato); FOC solo consume	F7, F12	[OBS]
C01-02	ib	C-01	PMSMBase	FOC B1.3	Planta	A	Fase b	[TBD]	[TBD]	Ídem	NO IMPLEMENTADO	Ídem	F7, F12	[OBS]
C01-03	ic	C-01	PMSMBase	FOC B1.3	Planta	A	Fase c	[TBD]	[TBD]	Ídem	NO IMPLEMENTADO	Ídem	F7, F12	[OBS]
C01-04	theta_m	C-01	PMSMBase (salida)	FOC B1.3	Planta	rad	Mecánica; theta_e = p·theta_m	Creciente con giro positivo [OBS]	No acotado en código observado	Ídem	NO IMPLEMENTADO	[TBD]	F7, F2 §21	[OBS] / CLOSED D-06 / A-02
C01-05	omega_m	C-01	PMSMBase	FOC B1.3	Planta	Rad/s	Velocidad angular mecánica del rotor	Positivo en giro positivo [OBS]	[TBD]	Ídem	NO IMPLEMENTADO	Planta (dato); FOC solo consume	F7, evidencia D-06	[OBS] / CLOSED D-06
C01-06	va	C-01	FOC B1.3	PMSMBase	FOC	V	Fase–neutro no verificado [TBD]	Bipolar [OBS]	[TBD]	Ídem	NO IMPLEMENTADO	FOC (actuación)	F7, F12	OBS — D-01
C01-07	vb	C-01	FOC B1.3	PMSMBase	FOC	V	Ídem	Bipolar	[TBD]	Ídem	NO IMPLEMENTADO	FOC	F7, F12	OBS — D-01
C01-08	vc	C-01	FOC B1.3	PMSMBase	FOC	V	Ídem	Bipolar	[TBD]	Ídem	NO IMPLEMENTADO	FOC	F7, F12	OBS — D-01
C02-xx	(ninguna)	C-02	—	—	—	—	—	—	—	—	—	—	—	[TBD] — no existen señales respaldadas
C03-xx	(ninguna)	C-03	—	—	—	—	—	—	—	—	—	—	—	[TBD]
C04-xx	(ninguna)	C-04	—	—	—	—	—	—	—	—	—	—	—	[TBD]
12. MATRIZ DE OWNERSHIP
Propietario = dueño lógico del dato/estado. Debe ser único por elemento.

Elemento	Propietario	Productor	Consumidores	Quién puede modificar	Estado
ia, ib, ic	Planta	PMSMBase	FOC B1.3	Solo la dinámica de la planta	[OBS]
theta_m	PMSMBase	PMSMBase (salida)	FOC B1.3	Planta	[OBS] / CLOSED D-06 / A-02
omega_m	PMSMBase	PMSMBase / PlantOutput.omega_m	FOC B1.3	Planta	CLOSED D-06
id, iq (estados dq de la planta)	Planta	PMSMBase	Ninguno en B1.3 (observables)	Solo la dinámica de la planta	OBS
id, iq (histórico: calculados en M3 y entregados al FOC)	M3 (histórico)	electrical_core	foc_core	—	[HIST]
id_ref	[TBD]	[TBD]	FOC B1.3	[TBD]	[CONFLICTING] — D-04
iq_ref	[TBD]	[TBD]	FOC B1.3	[TBD]	[CONFLICTING] — D-04, D-02
vd, vq	FOC histórico (producto interno)	foc_core / foc.py	M3 histórico	—	[HIST] — D-01
va, vb, vc	FOC B1.3	FOC B1.3	PMSMBase	FOC	OBS — D-01
omega_ref	[TBD]	— en B1.3; histórico: REF_BUS (constante en la raíz)	FOC histórico	—	[HIST] — D-02
VDC	[TBD]	— en el código activo; histórico: constante motor.VDC en M4	FOC histórico; M3 y M4 históricos	—	[HIST] — D-09
Límites (corriente, tensión, saturaciones)	[TBD]	—	—	—	[TBD]; históricos en el FOC reconstruido
Modos de operación	[TBD]	— en el código activo; histórico: modo_operacion (REF_BUS)	—	—	[HIST] / [TBD]
t_load	Entorno de simulación/ensayo	Harness	PMSMBase	Harness	[OBS]; en un sistema real: [TBD]
dt	Entorno de ejecución	Harness	PMSMBase; FOC B1.3	Harness	OBS
Parámetros de planta (F8)	Planta	parameters.py	PMSMBase	Solo por decisión documentada (fuente única F2)	[CONF]
Parámetros del FOC	FOC	—	FOC	[TBD]	B1.3: [TBD]; histórico: [HIST]
Integradores del FOC	FOC	FOC	FOC (internos)	FOC	[HIST] / OBS
13. MATRIZ DE AUTORIDAD
Estados: OWNER, PRODUCER, CONSUMER, ADVISORY, TBD, NOT_ALLOWED. — = sin relación evidenciada ni propuesta. La columna "Entorno" se añade porque t_load, dt y las referencias de ensayo provienen del harness.

Variable / función	Planta	FOC	MPC	ANFIS	TinyML	Entorno / harness
ia, ib, ic	OWNER, PRODUCER	CONSUMER	TBD	TBD	—	—
theta_m	PRODUCER: PMSMBase	CONSUMER: FOC B1.3	C-01	Planta	—	PlantInput.theta_m no pertenece al contrato activo
omega_m	PRODUCER: PMSMBase / PlantOutput.omega_m	CONSUMER: FOC B1.3	C-01	Planta	—	CLOSED D-06
va, vb, vc	CONSUMER	OWNER, PRODUCER	TBD	TBD	—	—
id_ref, iq_ref	—	CONSUMER (B1.3); en el histórico PRODUCER	TBD	TBD	—	TBD (en ensayos: constantes del harness)
omega_ref	—	TBD (inexistente en B1.3)	TBD	TBD	—	TBD
t_load	CONSUMER	—	—	—	—	OWNER, PRODUCER
dt	CONSUMER	CONSUMER	TBD	TBD	TBD	OWNER
VDC	TBD (excluido de la parametrización activa)	TBD	TBD	—	—	TBD
Límites del controlador (corriente/tensión)	—	TBD	TBD	TBD	—	—
Parámetros de planta	OWNER	—	TBD (consumo futuro)	TBD	—	—
Ganancias del FOC (kp, ki)	—	OWNER (B1.3: TBD)	TBD	TBD (histórico: Kp_adapt/Ki_adapt desde M7)	—	—
Actuación sobre la planta	CONSUMER	Único productor observado de va, vb, vc	TBD	No se asume control directo	No se asume	—
NOT_ALLOWED no se asigna a ninguna celda: no hay en la evidencia una prohibición contractual explícita; asignarla sería inventarla. La columna TinyML es — porque TinyML es tecnología de despliegue [PROP] sin autoridad propia evidenciada.

14. MATRIZ DE VALIDEZ
Estado general: NO IMPLEMENTADO — CONTRATO PROPUESTO. No se inventan códigos, enumeraciones, criterios ni umbrales.

Elemento	Mecanismo de validez existente	Estados con respaldo en la evidencia	Estados candidatos [PROP]	Criterios y umbrales
ia, ib, ic	Ninguno	Condición inicial definida (0 A) como configuración [CONF]; no hay estado INITIALIZING implementado	VALID, INVALID, UNAVAILABLE, INITIALIZING, STALE, OUT_OF_RANGE	[TBD]
theta_m, omega_m	Ninguno	Condición inicial definida (0) [CONF]	Estados de planta; la semántica/ownership de D-06/A-02 está cerrada. Los criterios de validez permanecen TBD	[TBD]
va, vb, vc	Ninguno (histórico: FAULT fijo en false, ENABLE en M3)	Ninguno	Ídem	[TBD]
Señales de C-02, C-03, C-04	—	No existen señales	—	[TBD]
Validaciones de software existentes (no son validez de señal): dt <= 0 → error en PMSMBase.step; PMSMParameters.validate() → coherencia de parámetros.

15. MATRIZ DE SEGURIDAD
Mecanismo / límite	Tipo	Valor	Fuente	Autoridad de protección	Estado
Límite de corriente en B1.3	Controlador	Ninguno implementado (decl.)	F1, F12	—	OBS
Límite de tensión en B1.3	Controlador	Ninguno implementado (decl.)	F1, F12	—	OBS
Límite de iq	Histórico (controlador)	±112.43 A	F9, F6	FOC histórico	[HIST] — no confirmado como contractual
Límite de tensión v_max	Histórico (controlador)	max(1, VDC)/√3 · 0.95	F9, F6	FOC histórico	[HIST] — D-09
Anti-windup por rollback	Histórico (controlador)	—	F9, F10, F6	FOC histórico	[HIST]
Saturación de duty	Histórico	[0, 1]	F6 (electrical_core)	M3 histórico	[HIST]
limites_activos	Histórico	[false,false,false,false] fijo	F6	M3 histórico	[HIST]
FAULT / ENABLE	Histórico	false fijo / paso directo de ENABLE_in	F6	M3 histórico	[HIST]
safety_mode (Guardian_Lyapunov)	Histórico	constante 0	F6 (M7)	M7 histórico	[HIST]
Fallback a FOC / ignorar predicción	Histórico/documental	—	F1 (Manifiesto, no adjunto)	—	[HIST] por segunda mano
Límite de convertidor	Histórico/documental	141 A	F1 (Manifiesto)	—	[HIST] por segunda mano
VDC	Histórico/documental	565 V	F1 (Manifiesto)	—	[HIST] por segunda mano — D-09
Valores nominales (53 A, 46 N·m, 471.24 rpm)	Configuración del modelo	—	F2 §5	—	[CONF]; no son límites físicos
Límite físico de la planta	Físico	—	—	—	[TBD]
Límite experimental	Experimental	—	—	—	[TBD]
Fallback / estado seguro / condición de fallo vigentes	—	—	—	—	[TBD]
16. ESTADOS INTERNOS VS SEÑALES DE INTERFAZ
Regla: un estado interno solo cruza una frontera si existe una razón arquitectónica documentada y una decisión explícita. Que exista en el código no es motivo.

Elemento	Módulo propietario	¿Cruza frontera?	Motivo	Estado
id, iq de la planta	Planta	No (observables)	El FOC B1.3 consume corrientes abc y transforma internamente	OBS
te	Planta	No (observable)	No lo consume el FOC; ecuación de referencia no verificada	[OBS]
omega_m (estado dinámico)	Planta PMSMBase	Sí, publicado como C01-05	Lo consume el FOC como velocidad mecánica en rad/s	CERRADO — D-06
theta_m (estado dinámico)	Planta PMSMBase	Sí, publicado como C01-04	Lo consume el FOC; sin doble rol contractual	CERRADO — D-06 / A-02
theta_e, omega_e	Cada módulo que los necesita	No	Derivados de p · theta_m y p · omega_m	[OBS]
Derivadas di_d, di_q, d_omega, d_theta	Planta	No	Cálculo interno de integración	[OBS]
Parámetros PMSMParameters	Planta	No	Configuración	[CONF]
Integradores PI de corriente d/q	FOC	No	Estado interno del controlador	[HIST] / OBS
Integrador de velocidad, contador de sub-muestreo, _iq_ref retenido	FOC histórico	No	Internos del FOC histórico	[HIST]
voltage_limit del PI	FOC histórico	No	Parámetro interno que foc.py fija en cada paso a partir de vdc	[HIST]
Parámetros térmicos y mapas recuperados	Planta	No	Almacenados; activación pendiente	[CONF] / PENDING VERIFICATION
17. REGISTRO D-01 … D-10
Todas las decisiones permanecen NO DECIDIDO. Las "opciones" son las que aparecen en la evidencia; no constituyen recomendación.

D-01 — Frontera eléctrica del FOC
Campo	Contenido
Decisión	Forma de la salida eléctrica del FOC / entrada eléctrica de la planta
Por qué importa al contrato	Define las señales de FOC→Planta en C-01 y qué módulo realiza la conversión y la normalización por VDC
Opciones	(a) (va, vb, vc); (b) (vd, vq) con una capa intermedia que convierta; (c) duty normalizado + VDC; (d) otra
Evidencia	(a) F7 PlantInput; F12 — [OBS]. (b) F9; F6 foc_core — [HIST]. (c) F6 electrical_core → pmsm_model — [HIST]. En F6 electrical_core las tensiones de fase son intermedias internas de M3
Decisión actual	NO DECIDIDO — [CONFLICTING]
D-02 — Autoridad del lazo de velocidad
Campo	Contenido
Decisión	Quién posee el lazo de velocidad y la generación de iq_ref a partir de omega_ref
Por qué importa	Determina si omega_ref existe en la interfaz del FOC y quién produce iq_ref (D-04)
Opciones	(a) dentro del FOC; (b) lazo externo (SpeedController); (c) fuera del alcance de C-01
Evidencia	F9 y F6 foc_core: PI de velocidad interno (kp 5.2804, ki 1.2693, 200 µs) — [HIST]. B1.3: sin lazo de velocidad en la interfaz — OBS. F3: "SpeedController externo" — mención
Decisión actual	NO DECIDIDO — [CONFLICTING]
D-03 — Archivos/módulos faltantes
Campo	Contenido
Decisión	Qué archivos o módulos deben incorporarse al conjunto de evidencia antes de congelar contratos
Por qué importa	Sin ellos, lo afirmado sobre B1.3, el desacoplamiento B1.2, las transformadas y los experimentos es de segunda mano
Opciones	No son opciones: es un inventario de ausencias
Evidencia	No adjuntos en esta revisión: fuente FOC B1.3; fuente desacoplamiento B1.2 (el decoupling.py adjunto se autodescribe como reconstrucción M6); scripts/resultados B1.4–B1.6 y B2.x; pmsm_hybrid_control/transforms/park.py (importado por pmsm_base.py); transforms/clarke.py (V1.0 lo cita como versión canónica; pmsm_base.py usa una Clarke local); Notas importantes; 01_construir_esqueleto; 02_CONTEXTO CONSOLIDADO; 05_CLOUDE_FORENSIC_REFERENCE; 06_KIMI_BUILD_RULES; Manifiesto ESDF v1.0
Decisión actual	NO DECIDIDO (V1.0 lo dejó "reservado" sin contenido)
D-04 — Autoridad sobre id_ref/iq_ref
Campo	Contenido
Decisión	Quién produce y quién posee id_ref e iq_ref
Por qué importa	Son entradas del FOC B1.3; sin propietario no hay contrato de referencias y C-02 no puede definirse
Opciones	(a) harness/entorno; (b) FOC interno; (c) MPC futuro; (d) otra capa
Evidencia	B1.3: entradas del FOC (decl.); B1.4: id_ref = 0, iq_ref = 10 en el harness (V1.0) — OBS. F9/F6 foc_core: salidas del FOC con id_ref = 0 fijo — [HIST]. F6 raíz: constantes id_ref_const = 0, iq_ref_const = 0 hacia REF_BUS; electrical_core también recibe id_ref, iq_ref como entradas — [HIST]
Decisión actual	NO DECIDIDO — [CONFLICTING]
D-05 — Velocidad nominal / histórica
Campo	Contenido
Decisión	Valor, unidad y significado de la velocidad nominal del M4
Por qué importa	Fija el rango y la unidad de omega_m (C2) y la referencia omega_ref histórica
Opciones	(a) 471.24 está en rpm (como etiqueta F2); (b) 471.24 corresponde a rad/s y el "4500 rpm" del Manifiesto expresa la misma magnitud; (c) otra interpretación
Evidencia	F2 §5, §24 y F8: 471.24 rpm — [CONF]. Manifiesto vía F1: 4500 rpm; debilitamiento >3100 rpm — [HIST] por segunda mano. Cruce aritmético: 4500 rpm × 2π/60 = 471.24 rad/s (A-04). F6: omega_ref_const = motor.omega_nominal (el valor de esa variable de workspace no está en el .slx) — [HIST]
Decisión actual	NO DECIDIDO. La coincidencia numérica no se toma como resolución
D-06 — Semántica y ownership de omega_m
Campo	Contenido
Decisión	Significado, unidad, referencia, productor, propietario y consumidores de omega_m
Por qué importa	Es señal de C-01 (C01-05); el desacoplamiento depende de omega_e = p · omega_m
Opciones	Dimensiones de decisión: mecánica vs. eléctrica; rad/s vs. rpm; propietario Planta (candidata [PROP]) vs. otro; filtrado o no
Evidencia	Ver 6.3. F7: mecánica en rad/s, sin transformación. F6: M4, M3 y foc_core usan omega_m mecánico y derivan omega_e = P · omega_m; existe bloque OmegaMechanical (1/motor.P) en M6, cableado no verificado. F12/F1: parche declarado en la migración (no localizable en lo adjunto)
Decisión actual	NO DECIDIDO. IMPLEMENTACIÓN ACTUAL PENDIENTE DE CORRECCIÓN CONTRACTUAL
D-07 — Estado y rol de MPC
Campo	Contenido
Decisión	Estado de MPC (documentado / propuesto / futuro) y su rol respecto del FOC
Por qué importa	Condiciona C-02 y la autoridad sobre referencias (D-04)
Opciones	(a) capa futura sin contrato hasta decidir; (b) entrega referencias al FOC; (c) genera la acción de control directamente; (d) otra
Evidencia	F4/F5: MPC como orquestador/ejecutor — [HIST]. F6: PLACEHOLDER_MPC dentro de M6 — [HIST]. F1: "discrepancia documental sobre MPC" en Notas importantes (no adjuntas) — [CONFLICTING]
Decisión actual	NO DECIDIDO. F3 define D-07 como "estado de MPC"; V1.0 lo dejó "reservado"
D-08 — Frecuencias históricas vs temporalidad observada
Campo	Contenido
Decisión	Qué periodos/frecuencias son contractuales y para qué módulo
Por qué importa	Define C3 de todos los contratos
Opciones	(a) congelar dt = 50 µs; (b) congelar frecuencias del Manifiesto; (c) definir periodos por módulo en un acto separado; (d) mantener dt como parámetro de ejecución sin frecuencia contractual
Evidencia	Observado: dt = 50 µs en B1.4/B2.x (V1.0) — OBS. Histórico: 20 kHz / 5 kHz / 1 kHz / 100 Hz (Manifiesto vía F1); RT_Speed 200 µs y RT_Supervisor 1 ms (F6); ts_current 50 µs y ts_speed 200 µs (F9); Ts = 50e-6 en CloudE (F2 §22)
Decisión actual	NO DECIDIDO. Frecuencia observada de ejecución ≠ frecuencia contractual
D-09 — VDC
Campo	Contenido
Decisión	A qué módulo pertenece VDC y si cruza alguna frontera
Por qué importa	El FOC histórico lo usa para el límite de tensión; la planta activa no lo contiene
Opciones	(a) parámetro de planta; (b) parámetro de un convertidor/módulo propio; (c) entrada del FOC; (d) excluido de C-01 (situación actual)
Evidencia	VDC no pertenece a la parametrización activa de la planta (F12; ausente en F7, F8). Histórico: FOC con v_max dependiente de vdc (F9); VDC_const = motor.VDC en M4 y duty normalizado por VDC en M3 (F6); 565 V (Manifiesto vía F1)
Decisión actual	NO DECIDIDO — [CONFLICTING]
D-10 — Ld/Lq constantes vs evolución a mapas/no linealidad
Campo	Contenido
Decisión	Cómo evolucionará M4_BASE sin romper las capas superiores
Por qué importa	Los contratos deben tolerar que Ld/Lq pasen de constantes a mapas
Opciones	(a) interfaz independiente de la forma de Ld/Lq; (b) revisar contratos al activar mapas
Evidencia	F2 §11: LdMatrix, LqMatrix constantes (1.2e-3 H) — [CONF] como almacenados; F2 §16–§19, §26: mapas y tablas recuperados con activación PENDING VERIFICATION; PmMatrix = 0.1 no se asume igual a λm; F3: la evolución no debe romper capas superiores
Decisión actual	NO DECIDIDO
18. CONFLICTOS ABIERTOS
18.1 Conflictos de la lista D
D-01, D-02, D-04, D-05, D-07, D-09, D-10: [CONFLICTING]. D-03: [TBD]. D-07 con componente [CONFLICTING], ver 17. D-06 y D-08 están cerrados. D-09 permanece abierto en su significado contractual de V2.0: ubicación de VDC.

18.2 Anomalías y conflictos adicionales detectados al reconstruir
Se numeran A-xx para no alterar D-01…D-10. Ninguno se resuelve.

ID	Fuente A	Fuente B	Diferencia	Impacto	Decisión necesaria
A-01	F8 e instrucciones: λm en Wb	F2 §3 y §24: λm en N·m·s/rad	Etiqueta de unidad distinta para el mismo valor 0.107245	C2 de parámetros de planta	Cuál es la unidad documental de λm
A-02	F7: theta_m es a la vez entrada (PlantInput, sobrescribe el estado) y estado/salida	F6 pmsm_model: theta_mem es estado propio, no entrada	Ownership de theta_m	C01-04, C4	Quién posee theta_m y de dónde proviene la entrada de la planta
A-03	F7/F8 (M4_BASE): λm 0.107245, sin B ni Tfric, entrada va/vb/vc, te con término de reluctancia (Ld−Lq)	F6 pmsm_model (histórico): λm 0.1100, B = 0.001, Tfric = 0.5, entrada duty+VDC, te = 1.5·P·λf·iq	El modelo Simulink histórico usa parámetros CloudE, no los M4 de F2	No usar F6 como fuente de parámetros de planta	Mantener F6 solo como [HIST]
A-04	F2/F8: 471.24 rpm	F1 (Manifiesto): 4500 rpm	4500 rpm = 471.24 rad/s (cruce aritmético)	Unidad y rango de omega_m	Ver D-05
A-05	F2 §5: nominales 53 A, 46 N·m	F7: Te = 1.5·p·λm·iq; con iq = 53 A, 1.5·4·0.107245·53 ≈ 34.1 N·m	Los nominales de F2 no se reconcilian por inspección directa con la ecuación de referencia; además F2 no indica si 53 A es pico o RMS (V1.0 afirmó "RMS" sin respaldo)	Valores nominales y base de amplitud de corriente	Confirmar significado de los nominales de F2 y verificar la ecuación de Te
A-06	F4/F5: MPC "ejecutor" y ANFIS como modelo predictivo, como controlador directo o como adaptador	F6: ANFIS entrega Kp_adapt/Ki_adapt al FOC; MPC placeholder dentro de M6	Roles de MPC y ANFIS distintos según la fuente	C-02, C-03	Ver D-07
A-07	F12: cadena Planta→FOC→MPC→ANFIS→TinyML	F4/F5/F6: FIS supervisor (FIS_Supervisor en M7)	La lógica difusa no tiene lugar en la cadena objetivo	Cobertura de fronteras	Ubicar o excluir FIS de la arquitectura
A-08	F12/F1: 50 µs "observado en Python actual"	F9, F6, F2 §22: 50 µs ya presente en el histórico/CloudE	El valor no distingue origen	D-08	Ver D-08
A-09	F7/F8: λm de planta 0.107245	F9/F6: λm del FOC 0.1100 (por defecto)	Parámetro de control ≠ parámetro de planta (≈ 2.6 %)	Parámetros del controlador	Valor usado en B1.2/B1.3: [TBD]
19. CRITERIOS DE ACEPTACIÓN CONTRACTUAL
19.1 Criterios de aceptación de este documento (V2.0)
#	Criterio	Cumplimiento en V2.0
1	C-01 representa Planta ↔ FOC	Sección 6.1: ocho señales; el resto en sección 5
2	id_ref, iq_ref, t_load y dt no se mezclan con la frontera física	NB-01…NB-04
3	omega_m permanece como problema contractual abierto	6.3, D-06
4	B1.3 y FOC histórico permanecen separados	6.14
5	Parámetros de planta separados de parámetros de controlador	6.12 y 6.13
6	Los buses históricos no se convierten en contratos activos	NB-16; sección 21
7	Las frecuencias históricas no se congelan	6.7, D-08
8	Los límites históricos no se convierten en confirmados	6.10, 15
9	C-02/C-03/C-04 sin señales inventadas	Secciones 7–9
10	D-01…D-10 trazables y abiertos	Sección 17
11	Toda decisión importante tiene origen/evidencia	Secciones 17 y 20
12	Sin código ni pseudocódigo	Todo el documento
19.2 Criterios para congelar cada contrato (condiciones previas)
Contrato	Condiciones para poder congelarse
C-01	(1) Cada señal tiene C1…C4 sin [TBD] esencial (propietario, unidad, referencia, signo); (2) D-01, D-05, D-06, D-08 y A-02 decididos; (3) fuente de B1.3 y de B1.2 incorporada a la evidencia (D-03); (4) cada afirmación OBS verificada contra su archivo; (5) experimentos con condición, resultado e interpretación registrados; (6) C5 y C6 definidos con alcance decidido, no heredado
C-02	D-04 y D-07 decididos; señales y autoridad respaldadas por decisión documentada
C-03	C-02 definido; rol de ANFIS decidido entre las lecturas de A-06
C-04	C-03 definido; evidencia de hardware, formato y métricas incorporada
20. MATRIZ DE TRAZABILIDAD
20.1 Afirmaciones y decisiones
Afirmación / decisión	Fuente	Ubicación	Experimento	Tipo	Estado de validación
C-01 = Planta ↔ FOC con ocho señales	F12	Instrucciones, secciones 3–4	—	Decisión de alcance	[HECHO]
Interfaz PlantInput/PlantOutput	F7	Clases	B1.x	Código	[OBS]
Interfaz FOC B1.3	F12, F1	Instrucciones; C-01 de V1.0	B1.4–B2.x	Declarada	OBS
Estructura B1.3 (Clarke→Park→PI→desacoplamiento→inversas)	F12	Instrucciones, sección 6	—	Declarada	OBS
Interfaz FOC histórico (omega_ref, omega_m, id, iq, vdc, dt)→(vd, vq, id_ref, iq_ref)	F9; F6	step; chart foc_core	—	Código histórico	[HIST]
Parámetros M4	F2, F8	F2 §2–§5, §24; parameters.py	—	Dato	[CONF]
λm = 0.107245 (procedencia PENDING), no 0.11	F2, F8	F2 §3, §22, §27	—	Dato	[CONF] / PENDING
B y Tfric pendientes y ausentes del balance	F2, F7, F8	F2 §23; _derivatives	—	Dato	PENDING
Ecuación de Te: de referencia, no verificada	F7	Docstring	—	Código	[OBS]
dt = 50 µs en ensayos	F1	C-01/C3 de V1.0	B1.4, B2.x	Declarada	OBS
Frecuencias 20k/5k/1k/100 Hz	F1 (Manifiesto)	Sec. 15 de V1.0	—	Histórica	[HIST]
RT_Speed 200 µs; RT_Supervisor 1 ms	F6	system_root	—	Histórica	[HIST]
Parche de omega_m	F12, F1	"Notas importantes"	B2.x (según F1)	Declarada	[CONFLICTING]
Doble rol de theta_m	F7	step	—	Código	[OBS]
Rol conceptual de MPC/ANFIS/TinyML	F4, F5	Secciones MPC y "mapa de convivencia"	—	Documento conceptual	[HIST]
Topología histórica M1–M7, buses y placeholders	F6	system_root, system_9, system_46, system_60, system_69	—	Modelo	[HIST]
20.2 Registro de experimentos (evidencia de comportamiento observado)
Cada experimento se registra como: experimento → condición → resultado → interpretación → estado de validación. Los experimentos no se convierten en requisitos arquitectónicos.

Experimento	Condición	Resultado	Interpretación	Estado de validación
B1.4 — lazo de corriente cerrado con PMSM (b1_4_closed_current_pmsm.py según V1.0)	id_ref = 0, iq_ref = 10, DT = 50e-6 (V1.0)	No adjunto	Ninguna autorizada. Solo puede indicar que la interfaz B1.3 operó bajo esa condición	OBS; resultado [TBD]
B1.5, B1.6	No adjuntos; condiciones no conocidas	No adjunto	—	[TBD]
B2.x	V1.0 lo asocia con el parche de omega_m	No adjunto	Ninguna autorizada	OBS / [TBD]
Cuando se incorporen los scripts y resultados (D-03), cada fila debe completarse con evidencia directa y mantener separado lo que el experimento demuestra de lo que el contrato requiere.

21. SEPARACIÓN EXPLÍCITA: ACTIVO / OBSERVADO / HISTÓRICO / PROPUESTO / TBD / CONFLICTING
21.1 Activo (implementación vigente)
Planta PMSMBase / M4_BASE y sus parámetros confirmados (F7, F8).
FOC B1.3 con desacoplamiento B1.2 (declarado; fuente no adjunta).
21.2 Observado
Interfaces de planta y FOC B1.3; theta_e = p · theta_m; Euler explícito; ausencia de B, Tfric y VDC en la planta; dt = 50 µs en ensayos (decl.); omega_m mecánica en rad/s producida por PMSMBase; theta_m como estado propio de la planta; PlantOutput como snapshot coherente de x[k+1]; ausencia de validadores y de límites en B1.3 (decl.).
21.3 Histórico (evidencia de procedencia, no contrato)
FOC M6/CloudE (foc.py, current_controller.py, decoupling.py, foc_core): interfaz (vd, vq, id_ref, iq_ref), PI de velocidad, límite de iq ±112.43 A, v_max con VDC, anti-windup, λm 0.1100, kp/ki.
skeleton.slx: módulos M1–M7, buses PLANTA/GATE/STATE/REF/CONTROL/ADAPT/SAFETY, placeholders MPC/ANFIS, RT_Speed 200 µs, RT_Supervisor 1 ms, planta con parámetros CloudE y entrada duty+VDC.
Manifiesto ESDF v1.0 (vía F1): TINY_BUS, DIAG_BUS, M8, 20 kHz / 5 kHz / 1 kHz / 100 Hz, VDC 565 V, límite de convertidor 141 A, debilitamiento >3100 rpm, 4500 rpm.
Documentos conceptuales F4/F5.
21.4 Propuesto
Arquitectura objetivo Planta→FOC→MPC→ANFIS→TinyML.
La propiedad de omega_m por la planta deja de ser propuesta: queda cerrada por D-06.
Estados de validez candidatos (sin criterios).
TinyML como tecnología de despliegue.
Euler explícito como método numérico (declarado PROPOSED en F7).
21.5 TBD
C-02, C-03, C-04 completos; latencia y dato atrasado en C-01; signos, rangos, resolución, referencia de tensión de fase; límites físicos y experimentales; fallback y estado seguro; valor de λm usado en B1.2/B1.3; ganancias y límites de B1.3; D-03, D-07, D-10.
21.6 Conflicting
D-01, D-02, D-04, D-05, D-07, D-09, D-10 y las A-01…A-09 que continúen abiertas según 18.2. D-06 y D-08 dejan de pertenecer a este conjunto por sus respectivos cierres contractuales. D-09 permanece abierto en su significado contractual de V2.0: ubicación de VDC.
22. DECISIONES NECESARIAS ANTES DE IMPLEMENTAR contracts.py
Esta sección enumera decisiones e insumos. No contiene diseño de implementación.

#	Decisión / insumo	Bloquea	Motivo	Qué se necesita
1	Incorporar los archivos faltantes (D-03)	Todo C-01	Lo afirmado sobre B1.3, B1.2, transformadas y experimentos es de segunda mano	Fuente de B1.3 y B1.2; transforms/*.py; scripts y resultados B1.x/B2.x; Notas importantes; documentos de contexto
2	D-01: forma de la frontera eléctrica	C01-06…08	Tres representaciones conviven	Decisión documentada con módulo responsable de la conversión
3	D-06 y A-02: semántica y ownership de omega_m y theta_m	C01-04, C01-05	Cierre realizado con evidencia directa del código activo y pruebas asociadas	CERRADO: omega_m mecánica en rad/s y propiedad de la planta; theta_m propiedad de la planta
4	D-05 y A-01/A-04/A-05: unidades y nominales	C2 de C-01	Etiquetas de unidad y valores nominales no reconciliados	Verificación contra el .slx M4 de origen (F2 §28)
5	D-08: temporalidad contractual	C3 de todos los contratos	50 µs observado vs históricas; necesidad de snapshot temporal coherente	CERRADO: PlantOutput es snapshot coherente de x[k+1]; dt permanece parámetro de ejecución y no señal de frontera
6	D-04 y D-02: autoridad de referencias y lazo de velocidad	Frontera FOC (C-02) y alcance del FOC	Propietario de id_ref/iq_ref indefinido	Decisión de autoridad
7	D-09: ubicación de VDC	C-01 / ubicación de VDC	La ubicación de VDC permanece sin cierre contractual	Trazar la ubicación de VDC sin reutilizar el identificador D-09 para theta_m
8	Alcance de C5 y C6 para C-01	C5, C6	Hoy no hay mecanismos; no deben heredarse del histórico	Decisión sobre qué estados de validez y qué límites son contractuales
9	D-07 y A-06: rol de MPC y ANFIS	C-02, C-03	Lecturas contradictorias	Decisión de rol y de sentido de flujo
10	A-07: ubicación de FIS	Cobertura de fronteras	Fuera de la cadena objetivo	Decisión de incluir o excluir
11	D-10: política ante Ld/Lq variables	Estabilidad de interfaces	Evolución futura de M4_BASE	Decisión de independencia de interfaz
12	Criterio de congelamiento	Todo	Evitar congelar con [TBD] esenciales	Aprobar 19.2
Observación [PROP]: C01-01…C01-03 (ia, ib, ic) son las señales de C-01 con menos conflictos abiertos en la evidencia disponible (pendientes de signo, referencia, base de amplitud y rango). Si se decide congelar por etapas, serían las candidatas naturales. theta_m y omega_m tienen ownership cerrado por D-06 / A-02. va, vb, vc continúan dependiendo de D-01. Los restantes aspectos de unidad, signo, rango y validez que no hayan sido cerrados permanecen TBD.

NOTA DE RECONCILIACIÓN DE IDENTIFICADORES D-09

En V2.0, la fila 7 de la sección 22 asociaba el identificador D-09 con la ubicación de VDC. El cierre contractual de theta_m corresponde a D-06 / A-02. Durante la reconstrucción posterior del repositorio, ese cierre fue registrado mediante un commit identificado como D-09. V2.1 conserva ambas referencias explícitamente para no reescribir retrospectivamente V2.0. La ubicación de VDC, que es el D-09 contractual de V2.0, permanece abierta.

ANEXO A — CAMBIOS ESTRUCTURALES RESPECTO DE V1.0
#	V1.0	Problema	V2.0
1	C-01 incluía id_ref, iq_ref, t_load, dt, id/iq, te	Mezclaba referencias, perturbaciones, parámetros de ejecución y observables con señales de frontera	C-01 = 8 señales; resto en sección 5
2	Tabla única con tipo "estado", "comando", "parámetro" en C-01	Categorías mezcladas	Taxonomía (4.2) y separación en secciones
3	"53 A RMS [HECHO]"	F2 no indica base de amplitud	Base no documentada [TBD]; A-05
4	"20 kHz [OBS] derivada del código, no del manifiesto"	50 µs también existe en el histórico/CloudE	Frecuencia observada de ejecución ≠ contractual; A-08
5	C5 definía VALID como "finitos", etc.	Inventaba criterios	NO IMPLEMENTADO — CONTRATO PROPUESTO; sin criterios
6	C-02 presumía que MPC "modificaría referencias" del FOC	Presunción no respaldada	Sentido de flujo [TBD]; lecturas en conflicto registradas
7	D-03 y D-07 "reservados"	F3 los define (archivos faltantes; estado de MPC)	Restablecidos
8	Sección 11 reservada sin contenido	Estructura incompleta	Eliminada; secciones renumeradas
9	Propósito de omega_m: "desacoplamiento y FF de velocidad"	"FF de velocidad" sin respaldo	Uso en B1.3 [TBD]; semántica abierta
10	te con consumidor "M5/DIAG"	Consumidor activo no evidenciado	Observable sin consumidor evidenciado
11	λm en Wb sin advertencia	F2 documenta N·m·s/rad	A-01
12	[CONF] = contradicción	Ambigüedad con "confirmado"	[CONF] = CONFIRMED; contradicción = [CONFLICTING]
13	skeleton.slx solo citado	No inspeccionado	Inspeccionado a nivel XML: planta histórica con parámetros CloudE, topología, placeholders, código embebido
14	Matriz de autoridad y de validez ausentes	Requeridas	Secciones 13 y 14
15	Experimentos sin estructura	Falta relación experimento→condición→resultado→interpretación→validación	20.2
16	Sin separación entre parámetros de planta y de controlador	Riesgo de sustitución	6.12 y 6.13; A-09
Documento contractual V2.0. No genera código. No modifica archivos del proyecto. Las marcas [TBD] y [CONFLICTING] son cierres prohibidos.

 
CONTROL DE REVISIÓN V2.1

V2.1 deriva documentalmente de C1-C7_CONTRATO_V2.0.md, preservado sin modificaciones en docs/contracts/historical/.

Cierres incorporados:
- D-06: omega_m = velocidad angular mecánica de la planta, rad/s; PMSMBase es propietario/productor; FOC es consumidor; no se introduce sensor/estimador.
- D-08: PlantOutput es un snapshot coherente de x[k+1]; dt continúa siendo parámetro de ejecución.
- Cierre posterior de theta_m: pertenece a PMSMBase; no es entrada de PlantInput; se publica mediante PlantOutput. El repositorio registró este cierre con identificador D-09, sin modificar el significado contractual de D-09 en V2.0.

No se consideran cerrados por esta revisión D-01, D-02, D-03, D-04, D-05, D-07 ni D-10.

V2.1 no autoriza por sí mismo la implementación de contratos.py, validadores ni nuevos mecanismos arquitectónicos. Se mantiene la secuencia: evidencia → decisión → cierre → interfaz → implementación, cuando corresponda → prueba → cierre.
