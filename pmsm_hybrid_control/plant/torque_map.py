"""MAPA DE TORQUE — Phase 2 (implementacion base CONSERVADORA).

Base analitica (PROPOSED, trazada a datos M4 CONFIRMED):
    Te = (3/2) * p * (lambda_m*iq + (Ld - Lq)*id*iq)   [REFERENCIA]
Es la misma ECUACION DE REFERENCIA usada en PMSMBase (PROMPT MAESTRO #13):
no se afirma que sea la ley interna exacta de Simscape M4 sin evidencia.

TorqueMatrix = zeros(3,3,3,4) esta CONFIRMED AS STORED PARAMETER
(01_M4_HARD_DATA.md#10) pero su ACTIVE STATUS bajo constantMutualInductance
es PENDING VERIFICATION: NO se usa como mapa activo.
"""
from __future__ import annotations

from .parameters import PMSMParameters, default_m4_parameters, TraceStatus


class TorqueMap:
    """Mapa de torque Te(id, iq). Base analitica de referencia (PROPOSED)."""

    STATUS = TraceStatus.PROPOSED
    SOURCE = "PROMPT MAESTRO #13 / 01_M4_HARD_DATA.md#2-3 (REFERENCIA)"

    def __init__(self, params: PMSMParameters | None = None,
                 use_recovered_tables: bool = False) -> None:
        if use_recovered_tables:
            raise NotImplementedError(
                "TorqueMatrix recuperada tiene ACTIVE STATUS = PENDING VERIFICATION."
            )
        self.params = params if params is not None else default_m4_parameters()
        self.params.validate()

    def evaluate(self, id_a: float, iq: float, theta_e: float = 0.0) -> float:
        """Torque electromagnetico [N*m] — ecuacion de referencia."""
        p = self.params
        return 1.5 * p.n_pole_pairs * (p.lambda_m * iq + (p.ld - p.lq) * id_a * iq)
