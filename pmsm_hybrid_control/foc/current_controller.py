"""CONTROLADOR DE CORRIENTE PI — PHASE 5 (NO IMPLEMENTADO).

No introducir ganancias definitivas sin especificarlas o derivarlas de
forma documentada (MASTER_SPEC #23). Ts = 50 us pertenece a CloudE y NO
es la frecuencia definitiva de los modulos Python (MASTER_SPEC #25).

ESTADO: PENDING — interfaz placeholder unicamente.
"""
from __future__ import annotations


class CurrentControllerNotImplementedError(NotImplementedError):
    pass


class CurrentController:
    """Interfaz placeholder para PI de corriente d/q con anti-windup."""

    def update(self, id_ref: float, iq_ref: float, id_meas: float, iq_meas: float,
               dt: float) -> tuple[float, float]:
        raise CurrentControllerNotImplementedError(
            "Controlador de corriente no implementado (Phase 5, tras M4_NONLINEAR)."
        )
