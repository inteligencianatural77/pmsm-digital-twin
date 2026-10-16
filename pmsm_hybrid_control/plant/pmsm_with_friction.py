"""Variante experimental PMSM con fricción no lineal.

Esta clase extiende PMSMBase sin modificar su implementación ni su contrato.

Propósito:
    introducir explícitamente un término de fricción experimental en la
    dinámica mecánica para estudiar su efecto sobre el control.

La fricción utilizada no representa todavía parámetros confirmados del
Siemens 1FT7087.

Balance mecánico:

    d(omega_m)/dt = (Te - T_load - Tf(omega_m)) / J

Con friction=None, la dinámica mecánica coincide con PMSMBase.
"""

from __future__ import annotations

from pmsm_hybrid_control.plant.friction import StribeckFriction
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase


class PMSMWithFriction(PMSMBase):
    """Variante experimental de PMSMBase con fricción explícita."""

    def __init__(
        self,
        friction: StribeckFriction | None = None,
        params=None,
    ) -> None:
        super().__init__(params=params)
        self.friction = friction

    def friction_torque(self) -> float:
        """Retorna el par de fricción aplicado en el estado actual."""
        if self.friction is None:
            return 0.0

        return self.friction.torque(self._omega_m)

    def _derivatives(
        self,
        vd: float,
        vq: float,
        t_load: float,
        omega_e: float,
    ) -> tuple[float, float, float, float]:
        """Calcula las derivadas con fricción mecánica explícita."""
        p = self.params

        di_d = (
            vd
            - p.rs * self._id
            + omega_e * p.lq * self._iq
        ) / p.ld

        di_q = (
            vq
            - p.rs * self._iq
            - omega_e * (p.ld * self._id + p.lambda_m)
        ) / p.lq

        te = self.electromagnetic_torque()
        tf = self.friction_torque()

        d_omega = (te - t_load - tf) / p.j
        d_theta = self._omega_m

        return di_d, di_q, d_omega, d_theta
