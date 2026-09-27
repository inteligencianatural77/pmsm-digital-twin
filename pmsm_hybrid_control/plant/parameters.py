"""Parametros confirmados del modelo M4 (PMSM 1FT7087).

FUENTE UNICA: 01_M4_HARD_DATA.md (M4 HARD DATA).
Los valores de CloudE (p. ej. lambda_m = 0.11, B = 0.001, Tfric = 0.5)
NO se utilizan aqui. Ver 05_CLOUDE_FORENSIC_REFERENCE.md.

Estado de trazabilidad:
- CONFIRMED: evidencia directa en datos del proyecto.
- PENDING VERIFICATION: referencia existe pero falta verificar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TraceStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROPOSED = "PROPOSED"                      # decision de diseno interna
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


@dataclass(frozen=True)
class TraceableValue:
    """Un valor numerico con estado de trazabilidad y fuente documentada."""
    value: float
    status: TraceStatus
    source: str
    unit: str
    note: str = ""


# ----------------------------------------------------------------------
# Parametros electricos M4 — CONFIRMED (01_M4_HARD_DATA.md, seccion 2-3)
# ----------------------------------------------------------------------
RS = TraceableValue(0.05, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#2", "ohm")
MS = TraceableValue(0.00002, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#2", "H")
L0 = TraceableValue(0.00016, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#2", "H")
LD = TraceableValue(0.0012, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#2", "H")
LQ = TraceableValue(0.0012, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#2", "H")

# lambda_m M4. NO sustituir por 0.11 (ese valor pertenece a CloudE).
# valor = CONFIRMED | procedencia exacta = PENDING VERIFICATION.
LAMBDA_M = TraceableValue(
    0.107245, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#3", "Wb",
    note="provenance=PENDING_VERIFICATION; NO usar CloudE lambda_m=0.11",
)

# ----------------------------------------------------------------------
# Parametros electromecanicos M4 — CONFIRMED (01_M4_HARD_DATA.md, seccion 4)
# ----------------------------------------------------------------------
N = TraceableValue(6, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#4", "-",
                   note="parametro del bloque; NO es numero de pares de polos")
N_POLE_PAIRS = TraceableValue(4, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#4", "-",
                              note="8 polos fisicos")
J = TraceableValue(0.00416, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#4", "kg*m^2")

# ----------------------------------------------------------------------
# Valores nominales — CONFIRMED como configuracion (seccion 5)
# ----------------------------------------------------------------------
ID_NOMINAL = TraceableValue(53.0, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#5", "A")
IQ_NOMINAL = TraceableValue(53.0, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#5", "A")
TORQUE_NOMINAL = TraceableValue(46.0, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#5", "N*m")
OMEGA_NOMINAL_RPM = TraceableValue(471.24, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#5", "rpm")

# ----------------------------------------------------------------------
# Parametros termicos — CONFIRMED como parametros almacenados (seccion 15)
# La dinamica termica NO se implementa en Phase 1.
# ----------------------------------------------------------------------
ALPHA = TraceableValue(3.93e-3, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#15", "1/K")
ALPHA_FLUX = TraceableValue(-0.001, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#15", "1/K")
T_MEAS = TraceableValue(298.15, TraceStatus.CONFIRMED, "01_M4_HARD_DATA.md#15", "K")

# ----------------------------------------------------------------------
# Parametros PENDING — NO INVENTAR (kimi build rules, seccion 9)
# CloudE tiene B=0.001 y Tfric=0.5, pero pertenecen a CloudE, NO a M4.
# ----------------------------------------------------------------------
B_PENDING = TraceableValue(float("nan"), TraceStatus.PENDING_VERIFICATION,
                           "06_KIMI_BUILD_RULES.md#9", "N*m*s/rad",
                           note="CloudE B=0.001 NO es parametro M4")
TFRIC_PENDING = TraceableValue(float("nan"), TraceStatus.PENDING_VERIFICATION,
                               "06_KIMI_BUILD_RULES.md#9", "N*m",
                               note="CloudE Tfric=0.5 NO es parametro M4")


@dataclass(frozen=True)
class PMSMParameters:
    """Contenedor de parametros confirmados del M4 base.

    Solo contiene valores CONFIRMED de 01_M4_HARD_DATA.md.
    Los parametros pendientes (B, Tfric) se exponen como PENDING y no
    participan en el modelo hasta ser verificados.
    """
    rs: float = RS.value
    ms: float = MS.value
    l0: float = L0.value
    ld: float = LD.value
    lq: float = LQ.value
    lambda_m: float = LAMBDA_M.value
    n: float = N.value
    n_pole_pairs: int = int(N_POLE_PAIRS.value)
    j: float = J.value

    def validate(self) -> None:
        """Validacion basica de coherencia de parametros confirmados."""
        if self.rs <= 0:
            raise ValueError("Rs debe ser positivo (Rs = 0.05 ohm CONFIRMED)")
        if self.ld <= 0 or self.lq <= 0:
            raise ValueError("Ld y Lq deben ser positivas")
        if self.lambda_m <= 0:
            raise ValueError("lambda_m debe ser positivo")
        if self.j <= 0:
            raise ValueError("J debe ser positivo")
        if self.n_pole_pairs != 4:
            raise ValueError("nPolePairs = 4 es CONFIRMED para M4")

    @property
    def pending_parameters(self) -> dict[str, TraceableValue]:
        """Parametros que existen como referencia pero NO estan confirmados para M4."""
        return {"B": B_PENDING, "Tfric": TFRIC_PENDING}


def default_m4_parameters() -> PMSMParameters:
    """Construye el conjunto de parametros M4 confirmados por defecto."""
    p = PMSMParameters()
    p.validate()
    return p
