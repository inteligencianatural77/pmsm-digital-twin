"""VALIDACION ANFIS — PHASE 3 (NO IMPLEMENTADO).

La comparacion REFERENCE MAP vs ANFIS con metricas (RMSE, MAE, error
absoluto/relativo) se definira aqui. Tolerancias oficiales: PENDING.
ESTADO: PENDING — interfaz placeholder."""
from __future__ import annotations


class ANFISValidationNotImplementedError(NotImplementedError):
    pass


def validate_surrogate(*args, **kwargs):
    raise ANFISValidationNotImplementedError("Validacion ANFIS no implementada (Phase 3).")
