"""GOVERNOR / ADAPTATION — PHASE 7-8 (NO IMPLEMENTADO).

Elementos CloudE asociados (M6 Adaptive Selector sin salida visible,
ADAPT_BUS con campos PENDING) se registran como observaciones, NO se
migran automaticamente (05_CLOUDE_FORENSIC_REFERENCE.md#10-13, #25).
ESTADO: PENDING — interfaz placeholder."""
from __future__ import annotations


class GovernorNotImplementedError(NotImplementedError):
    pass


class Governor:
    """Interfaz placeholder de adaptation/governor."""

    def update(self, *args, **kwargs):
        raise GovernorNotImplementedError("Governor no implementado (Phase 7).")
