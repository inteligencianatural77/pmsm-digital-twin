"""SURROGATE ANFIS — PHASE 3 (NO IMPLEMENTADO).
ESTADO: PENDING — interfaz placeholder."""

from __future__ import annotations


class SurrogateNotImplementedError(NotImplementedError):
    pass


class ANFISSurrogate:
    """Interfaz placeholder para inferencia del sustituto ANFIS."""

    def predict(self, *args, **kwargs):
        raise SurrogateNotImplementedError("Surrogate ANFIS no implementado (Phase 3).")
