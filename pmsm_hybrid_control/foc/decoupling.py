"""DESACOPLAMIENTO dq — PHASE 5 (NO IMPLEMENTADO).

ESTADO: PENDING — interfaz placeholder.
"""
from __future__ import annotations


class DecouplingNotImplementedError(NotImplementedError):
    pass


class Decoupling:
    """Interfaz placeholder para desacoplamiento de ejes d/q."""

    def apply(self, vd_pi: float, vq_pi: float, id_: float, iq: float,
              omega_e: float, ld: float, lq: float, lambda_m: float) -> tuple[float, float]:
        raise DecouplingNotImplementedError("Decoupling no implementado (Phase 5).")
