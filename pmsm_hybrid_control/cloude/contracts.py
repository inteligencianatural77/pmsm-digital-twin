"""CONTRATOS CLOUDE — PHASE 9 (placeholder).

Buses CloudE (CONTROL_BUS, REF_BUS, ADAPT_BUS, Safety BUS) son referencia
arquitectonica. Su mapping a Python es PENDING VERIFICATION.
ESTADO: PENDING."""
from __future__ import annotations

from enum import Enum


class BusStatus(str, Enum):
    CONFIRMED = "CONFIRMED"                    # el bus existe en CloudE
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


# Buses CONFIRMED como existentes en CloudE (05_CLOUDE_FORENSIC_REFERENCE.md#36)
CLOUDE_BUSES = {
    "CONTROL_BUS": BusStatus.CONFIRMED,
    "REF_BUS": BusStatus.CONFIRMED,
    "ADAPT_BUS": BusStatus.CONFIRMED,          # campos PENDING
    "Safety BUS": BusStatus.PENDING_VERIFICATION,  # parcialmente conectado
}

# Equivalencia CONTROL_BUS <-> REF_BUS: PENDING (no asumir).
# lambda_m: M4 = 0.107245 (NO igualar al de CloudE = 0.11).
