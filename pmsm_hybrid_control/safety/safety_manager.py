"""SAFETY MANAGER — PHASE 8 (NO IMPLEMENTADO).

El Safety BUS de CloudE esta parcialmente conectado (CONFIRMED OBSERVATION,
05_CLOUDE_FORENSIC_REFERENCE.md#23). Antes de mapearlo deben definirse
conditions, limits, priority, actions, fault states. ESTADO: PENDING."""
from __future__ import annotations


class SafetyManagerNotImplementedError(NotImplementedError):
    pass


class SafetyManager:
    """Interfaz placeholder del gestor de seguridad."""

    def check(self, *args, **kwargs):
        raise SafetyManagerNotImplementedError(
            "Safety Manager no implementado. Definir conditions/limits/actions primero."
        )
