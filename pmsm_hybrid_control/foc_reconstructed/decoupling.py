"""Desacoplamiento dq reconstruido a partir del M6/Foc Core de CloudE."""

from __future__ import annotations


class Decoupling:
    """Términos cruzados de tensión del modelo PMSM."""

    @staticmethod
    def apply(
        id_: float,
        iq: float,
        omega_e: float,
        ld: float,
        lq: float,
        lambda_m: float,
    ) -> tuple[float, float]:

        vd = -omega_e * lq * iq
        vq = omega_e * (ld * id_ + lambda_m)

        return vd, vq
