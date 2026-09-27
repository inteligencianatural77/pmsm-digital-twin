"""PLANTA NO LINEAL — PHASE 4 (NO IMPLEMENTADO).

Combinara PMSMBase + mapas no lineales + surrogate ANFIS opcional
(MASTER_SPEC #20). La separacion M4_BASE vs M4_NONLINEAR debe permitir
comparar ambas en las mismas condiciones.

ESTADO: PENDING — interfaz placeholder unicamente.
"""
from __future__ import annotations

from .pmsm_base import PMSMBase


class PMSMNonlinearNotImplementedError(NotImplementedError):
    pass


class PMSMNonlinear:
    """Interfaz placeholder. Envuelve PMSMBase; extension pendiente."""

    def __init__(self, base: PMSMBase) -> None:
        self.base = base  # referencia para futura composicion

    def step(self, *args, **kwargs):
        raise PMSMNonlinearNotImplementedError(
            "M4_NONLINEAR no implementado (Phase 4, despues de MAPAS y ANFIS)."
        )
