"""MAPAS DE FLUJO — Phase 2 (implementacion base CONSERVADORA).

Dos fuentes posibles, claramente separadas:

1. BASE ANALITICA (activa por defecto) — PROPOSED:
   Derivada EXCLUSIVAMENTE de parametros M4 CONFIRMED con la parametrizacion
   confirmada `constantMutualInductance` (01_M4_HARD_DATA.md#1-2):
       psi_d = Ld * id + lambda_m
       psi_q = Lq * iq
   Con Ld = Lq (CONFIRMED), este mapa es lineal y sin saliencia.
   Estado: PROPOSED (representacion interna), trazado a 01_M4_HARD_DATA.md.

2. TABLAS RECUPERADAS (inactivas) — RECOVERED / PENDING VERIFICATION:
   dfluxdiMatrix, dfluxdxMatrix, dfluxAdiaMatrix3D, fluxD_dq0, fluxD_IBX, ...
   (01_M4_HARD_DATA.md#8-18). Su ACTIVE STATUS bajo constantMutualInductance
   es PENDING VERIFICATION: NO se usan automaticamente como mapas activos.
   Se cargan solo como datos recuperados con su estado visible.

NO se construye un solver FEM (06_KIMI_BUILD_RULES.md#7).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .parameters import PMSMParameters, default_m4_parameters, TraceStatus


@dataclass(frozen=True)
class RecoveredTable:
    """Tabla recuperada del .slx con su estado de activacion."""
    name: str
    data: np.ndarray
    status: TraceStatus = TraceStatus.PENDING_VERIFICATION
    source: str = "01_M4_HARD_DATA.md"


def recovered_m4_tables() -> dict[str, RecoveredTable]:
    """Tablas recuperadas del modelo M4. ACTIVE STATUS = PENDING VERIFICATION.

    NO usar como mapas activos hasta verificar su semantica bajo
    constantMutualInductance (02_CONTRACTS.md#7.1).
    """
    deg = np.pi / 180.0
    return {
        "iVec": RecoveredTable("iVec", np.array([-2.0, 0.0, 2.0]), source="#7"),
        "xVec": RecoveredTable("xVec", np.array([0.0, 20.0, 40.0, 60.0]) * deg, source="#7"),
        "dfluxdiMatrix": RecoveredTable(
            "dfluxdiMatrix", 0.0002 * np.ones((3, 4)), source="#8"),
        "dfluxdxMatrix": RecoveredTable(
            "dfluxdxMatrix",
            np.array([[0.0, -0.16, 0.16, 0.0]] * 3), source="#9"),
        "TorqueMatrix": RecoveredTable(
            "TorqueMatrix", np.zeros((3, 3, 3, 4)), source="#10"),
        "LdMatrix": RecoveredTable(
            "LdMatrix", 1.2e-3 * np.ones((3, 3)), source="#11"),
        "LqMatrix": RecoveredTable(
            "LqMatrix", 1.2e-3 * np.ones((3, 3)), source="#11"),
        "PmMatrix": RecoveredTable(
            "PmMatrix", 0.1 * np.ones((3, 3)), source="#12"),
        "dfluxAdiaMatrix3D": RecoveredTable("dfluxAdiaMatrix3D", None, source="#16"),
        "fluxD_dq0": RecoveredTable("fluxD_dq0", np.zeros((3, 3, 7)), source="#17"),
        "fluxQ_dq0": RecoveredTable("fluxQ_dq0", np.zeros((3, 3, 7)), source="#17"),
        "fluxA_dq0": RecoveredTable("fluxA_dq0", np.zeros((3, 3, 7)), source="#17"),
        "Torque_dq0": RecoveredTable("Torque_dq0", np.ones((3, 3, 7)), source="#17"),
        "fluxD_IBX": RecoveredTable("fluxD_IBX", np.zeros((3, 5, 7)), source="#18"),
        "fluxQ_IBX": RecoveredTable("fluxQ_IBX", np.zeros((3, 5, 7)), source="#18"),
        "fluxA_IBX": RecoveredTable("fluxA_IBX", np.zeros((3, 5, 7)), source="#18"),
        "Torque_IBX": RecoveredTable("Torque_IBX", np.zeros((3, 5, 7)), source="#18"),
        "rotorLossCoeff_k_h_DQ": RecoveredTable("rotorLossCoeff_k_h_DQ", np.zeros((3, 3)), source="#19"),
        "rotorLossCoeff_k_J_DQ": RecoveredTable("rotorLossCoeff_k_J_DQ", np.zeros((3, 3)), source="#19"),
        "rotorLossCoeff_k_ex_DQ": RecoveredTable("rotorLossCoeff_k_ex_DQ", np.zeros((3, 3)), source="#19"),
    }


class FluxMap:
    """Mapa de flujo psi(id, iq).

    Por defecto usa la base analitica PROPOSED derivada de parametros M4
    CONFIRMED (Ld, Lq, lambda_m). Sin dependencia de theta: la variante
    constantMutualInductance CONFIRMADA no representa variacion con posicion
    (dfluxdxMatrix recuperada = PENDING, no activa).
    """

    STATUS = TraceStatus.PROPOSED
    SOURCE = "01_M4_HARD_DATA.md#1-3 (parametrizacion constantMutualInductance)"

    def __init__(self, params: PMSMParameters | None = None,
                 use_recovered_tables: bool = False) -> None:
        if use_recovered_tables:
            raise NotImplementedError(
                "Tablas recuperadas tienen ACTIVE STATUS = PENDING VERIFICATION "
                "(02_CONTRACTS.md#7.1). No activar sin verificacion documentada."
            )
        self.params = params if params is not None else default_m4_parameters()
        self.params.validate()

    def flux_d(self, id_a: float, iq: float = 0.0, theta_e: float = 0.0) -> float:
        """Flujo concatenado eje d [Wb]: psi_d = Ld*id + lambda_m."""
        return self.params.ld * id_a + self.params.lambda_m

    def flux_q(self, id_a: float = 0.0, iq: float = 0.0, theta_e: float = 0.0) -> float:
        """Flujo concatenado eje q [Wb]: psi_q = Lq*iq."""
        return self.params.lq * iq

    def evaluate(self, id_a: float, iq: float, theta_e: float = 0.0) -> tuple[float, float]:
        """(psi_d, psi_q) [Wb]."""
        return self.flux_d(id_a, iq, theta_e), self.flux_q(id_a, iq, theta_e)
