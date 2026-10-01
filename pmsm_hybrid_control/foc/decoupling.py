"""Desacoplamiento dq del FOC activo.

B1.2 — implementación activa.

El componente recibe la salida del PI de corriente y añade los términos
de compensación cruzada del modelo PMSM:

    vd_dec = -omega_e * Lq * iq
    vq_dec =  omega_e * (Ld * id + lambda_m)

Los parámetros de inductancia y flujo son recibidos explícitamente para
mantener la trazabilidad del componente y evitar introducir valores
históricos de forma implícita.

El valor M4 de lambda_m (0.107245 Wb) debe ser proporcionado por la capa
que construye el FOC. El valor histórico 0.1100 Wb no se incorpora como
default.
"""

from __future__ import annotations


class DecouplingNotImplementedError(NotImplementedError):
    """Compatibilidad con la interfaz placeholder histórica."""

    pass


class Decoupling:
    """Compensación de desacoplamiento de los ejes d/q."""

    def apply(
        self,
        vd_pi: float,
        vq_pi: float,
        id_: float,
        iq: float,
        omega_e: float,
        ld: float,
        lq: float,
        lambda_m: float,
    ) -> tuple[float, float]:
        """Añade los términos de desacoplamiento a la salida del PI.

        Parameters
        ----------
        vd_pi, vq_pi:
            Tensiones producidas por el PI de corriente [V].
        id_, iq:
            Corrientes d/q medidas [A].
        omega_e:
            Velocidad eléctrica [rad/s].
        ld, lq:
            Inductancias d/q [H].
        lambda_m:
            Flujo del imán permanente [Wb].

        Returns
        -------
        tuple[float, float]
            Tensiones finales ``vd`` y ``vq`` antes de la etapa de
            limitación/vectorización de tensión [V].
        """
        vd_dec = -float(omega_e) * float(lq) * float(iq)
        vq_dec = float(omega_e) * (
            float(ld) * float(id_) + float(lambda_m)
        )

        vd = float(vd_pi) + vd_dec
        vq = float(vq_pi) + vq_dec

        return vd, vq
