"""Controlador PI de velocidad para el FOC activo.

B2.1 — componente de control de velocidad.

La estructura del PI y sus valores por defecto proceden de la
reconstrucción histórica del lazo M6:

    Kp_w = 5.2804
    Ki_w = 1.2693

El controlador genera una referencia iq_ref para el FOC de corriente.

El límite aplicado corresponde exclusivamente a iq_ref. No representa
una limitación dura de la corriente física de la PMSM.

Referencia histórica:
    historical/closed_loop_reconstruction/lazo_cerrado_m3_foc_m4.py

Límites históricos:
    iq_ref_min = -112.43 A
    iq_ref_max = +112.43 A
"""

from __future__ import annotations


class SpeedController:
    """PI discreto de velocidad con límite de iq_ref y anti-windup."""

    def __init__(
        self,
        kp_w: float = 5.2804,
        ki_w: float = 1.2693,
        iq_ref_min: float = -112.4300,
        iq_ref_max: float = 112.4300,
    ) -> None:
        if iq_ref_min > iq_ref_max:
            raise ValueError("iq_ref_min debe ser menor o igual que iq_ref_max")

        self.kp_w = float(kp_w)
        self.ki_w = float(ki_w)
        self.iq_ref_min = float(iq_ref_min)
        self.iq_ref_max = float(iq_ref_max)

        self.int_w = 0.0
        self.iq_ref_state = 0.0

    def reset(self) -> None:
        """Reinicia el estado integral y la referencia de salida."""
        self.int_w = 0.0
        self.iq_ref_state = 0.0

    def update(
        self,
        omega_ref: float,
        omega_meas: float,
        dt: float,
    ) -> float:
        """Calcula una nueva referencia iq_ref.

        Parameters
        ----------
        omega_ref:
            Referencia de velocidad mecánica [rad/s].
        omega_meas:
            Velocidad mecánica medida [rad/s].
        dt:
            Paso temporal de actualización del PI [s].

        Returns
        -------
        float
            Referencia de corriente iq [A].

        Notes
        -----
        La saturación se aplica a la referencia ``iq_ref``.
        Si ocurre saturación, se deshace la integración realizada
        durante este paso, reproduciendo el anti-windup por rollback
        de la implementación histórica.
        """
        if dt <= 0.0:
            raise ValueError("dt debe ser positivo")

        error_w = float(omega_ref) - float(omega_meas)

        self.int_w += error_w * dt

        iq_ref_raw = (
            self.kp_w * error_w
            + self.ki_w * self.int_w
        )

        iq_ref = max(
            self.iq_ref_min,
            min(self.iq_ref_max, iq_ref_raw),
        )

        if iq_ref != iq_ref_raw:
            self.int_w -= error_w * dt

        self.iq_ref_state = float(iq_ref)

        return self.iq_ref_state
