"""Controlador PI de corriente dq.

B1.1 — implementación activa del controlador de corriente.

Las ganancias por defecto corresponden a los valores documentados del
FOC/M6 reconstruido:

    Kp_id = Kp_iq = 15.0796
    Ki_id = Ki_iq = 628.3185

Estos valores son una referencia histórica/documental del controlador M6.
NO son parámetros de la planta M4 ni implican que sean la sintonía
definitiva del FOC Python.

El desacoplamiento dq se mantiene fuera de este componente y se recibe
como término de tensión adicional.
"""

from __future__ import annotations


class CurrentControllerNotImplementedError(NotImplementedError):
    """Compatibilidad con la interfaz placeholder histórica."""

    pass


class CurrentController:
    """PI discreto de corriente d/q con anti-windup por rollback."""

    def __init__(
        self,
        kp_id: float = 15.0796,
        ki_id: float = 628.3185,
        kp_iq: float = 15.0796,
        ki_iq: float = 628.3185,
        voltage_limit: float | None = None,
    ) -> None:
        self.kp_id = float(kp_id)
        self.ki_id = float(ki_id)
        self.kp_iq = float(kp_iq)
        self.ki_iq = float(ki_iq)
        self.voltage_limit = (
            None if voltage_limit is None else float(voltage_limit)
        )

        self.int_id = 0.0
        self.int_iq = 0.0

    def reset(self) -> None:
        """Reinicia los estados integrales del controlador."""
        self.int_id = 0.0
        self.int_iq = 0.0

    def update(
        self,
        id_ref: float,
        iq_ref: float,
        id_meas: float,
        iq_meas: float,
        dt: float,
        decoupling_d: float = 0.0,
        decoupling_q: float = 0.0,
    ) -> tuple[float, float]:
        """Calcula las referencias de tensión vd/vq del PI.

        Parameters
        ----------
        id_ref, iq_ref:
            Referencias de corriente en el marco dq [A].
        id_meas, iq_meas:
            Corrientes medidas en dq [A].
        dt:
            Paso temporal de integración [s].
        decoupling_d, decoupling_q:
            Términos de compensación de desacoplamiento [V].

        Returns
        -------
        tuple[float, float]
            Tensiones ``vd`` y ``vq`` [V].
        """
        if dt <= 0.0:
            raise ValueError("dt debe ser positivo")

        error_id = float(id_ref) - float(id_meas)
        error_iq = float(iq_ref) - float(iq_meas)

        # Integración explícita.
        self.int_id += error_id * dt
        self.int_iq += error_iq * dt

        vd_raw = (
            self.kp_id * error_id
            + self.ki_id * self.int_id
            + float(decoupling_d)
        )

        vq_raw = (
            self.kp_iq * error_iq
            + self.ki_iq * self.int_iq
            + float(decoupling_q)
        )

        if self.voltage_limit is None:
            return float(vd_raw), float(vq_raw)

        if self.voltage_limit < 0.0:
            raise ValueError("voltage_limit no puede ser negativo")

        vd = max(-self.voltage_limit, min(self.voltage_limit, vd_raw))
        vq = max(-self.voltage_limit, min(self.voltage_limit, vq_raw))

        # Anti-windup por rollback: si un eje saturó, se deshace
        # únicamente la integración realizada en este paso.
        if vd != vd_raw:
            self.int_id -= error_id * dt

        if vq != vq_raw:
            self.int_iq -= error_iq * dt

        return float(vd), float(vq)
