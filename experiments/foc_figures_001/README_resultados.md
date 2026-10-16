# Resultados de figuras FOC — paquete 001

## Propósito

Figuras generadas desde CSV existentes. No se modificaron los ensayos ni los módulos de producción al generar estas gráficas.

## Inventario de figuras

| Archivo base | Contenido | Uso e interpretación |
|---|---|---|
| `b0.1_current_tracking` | Referencias y corrientes d-q del ensayo B0.1 | Evidencia histórica de seguimiento con `foc_reconstructed`. |
| `b0.1_voltage_margin` | Tensiones d-q y límite registrado | Verifica el margen de tensión de ese CSV. |
| `b0.2_current_tracking` | Referencias y corrientes d-q del ensayo B0.2 | Repite B0.1 usando `plant.params.lambda_m` en el desacoplamiento. |
| `b0.2_voltage_margin` | Tensiones d-q y límite registrado | Verifica el margen de tensión de ese CSV. |
| `b1.5_current_tracking` | Referencias y corrientes d-q por escalones | Seguimiento de corriente con el FOC activo. |
| `b1_6_load_response` | Carga, par, corriente q y velocidad | Respuesta mecánica ante cambios de carga con referencia de corriente fija. |
| `b0_1_b0_2_comparison` | Comparación de corriente q entre B0.1 y B0.2 | Visualiza la diferencia entre ambos ensayos históricos. |

Cada figura está disponible en PNG y PDF.

## Condiciones documentadas

### B0.1 y B0.2

- Paso temporal: 50 microsegundos.
- Duración: 50 ms.
- Referencia: iq pasa de 0 a 10 A a partir de 1 ms.
- Bus de referencia histórica: 600 V.
- Límite registrado: 0.95 VDC / raíz de 3.
- Controlador importado: `pmsm_hybrid_control.foc_reconstructed.current_controller.CurrentController`.
- B0.1 usa lambda_m = 0.107245 Wb como literal en el desacoplamiento.
- B0.2 usa `plant.params.lambda_m`.

### B1.5

- FOC activo: `pmsm_hybrid_control.foc.foc.FOC`.
- Referencia iq: 0, 10, 20 y 10 A en los instantes 0, 50, 100 y 150 ms.
- Carga: 0 Nm.
- El CSV no contiene vd, vq ni vmax; por tanto, esta figura no permite verificar directamente la saturación vectorial de tensión.

### B1.6

- FOC activo.
- Referencia iq fija: 10 A.
- Carga: 0, 5, 10 y 5 Nm en los instantes 0, 50, 100 y 150 ms.
- La velocidad es una respuesta del sistema, no una referencia regulada por un lazo de velocidad en este ensayo.

## Métricas de B0.1 y B0.2

- **B0.1:** RMSE global de iq = 0.34072 A; RMSE para t >= 3 ms = 0.01817 A; error final = -0.02567 A; máximo |iq| = 10.02567 A.
- **B0.2:** RMSE global de iq = 0.34027 A; RMSE para t >= 3 ms = 0.00101 A; error final = -0.00204 A; máximo |iq| = 10.00204 A.

## Hallazgos y límites

1. B0.1 y B0.2 son ensayos del controlador reconstruido y deben identificarse como tales; no son una validación del FOC activo.
2. En ambos CSV, el máximo registrado de |vdq|/vmax es aproximadamente 0.4592. La tensión se mantiene por debajo del límite registrado en estas condiciones.
3. B0.1 y B0.2 son pruebas muy parecidas; la diferencia entre ellas no debe presentarse como una comparación extensa de controladores.
4. B1.5 documenta el seguimiento de referencias de corriente con el FOC activo.
5. B1.6 documenta la respuesta ante carga con referencia de corriente fija. El par máximo informado es aproximadamente 6.4347 Nm, menor que el escalón de carga de 10 Nm; la velocidad cae. Esto no equivale a regulación de velocidad constante.
6. Estas figuras respaldan pruebas funcionales concretas. Por sí solas no validan el Digital Twin frente a datos experimentales del motor real ni demuestran cumplimiento térmico o de límites operativos del fabricante.

## Alcance para la tesis

Usar las figuras B1.5 y B1.6 para explicar el comportamiento del FOC activo. Las figuras B0.1 y B0.2 pueden conservarse como evidencia de desarrollo claramente separada. Antes de incorporar las figuras a la versión final de tesis, revisar legibilidad, pies de figura, referencias en el texto y coherencia con la metodología.
