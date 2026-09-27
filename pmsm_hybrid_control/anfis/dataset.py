"""DATASET ANFIS — PHASE 3 (NO IMPLEMENTADO).

El dataset debe definirse explicitamente (inputs, targets, metadata) y la
eleccion exacta de entradas/salidas ANFIS es PENDING VERIFICATION
(02_CONTRACTS.md#8; MASTER_SPEC #17). Candidatos conceptuales:
X=[id,iq,theta], Y=[psi_d,psi_q,Te] — NO son contrato definitivo.

ESTADO: PENDING — interfaz placeholder.
"""
from __future__ import annotations


class DatasetNotImplementedError(NotImplementedError):
    pass


class ANFISDataset:
    """Interfaz placeholder para dataset ANFIS."""

    def build(self, *args, **kwargs):
        raise DatasetNotImplementedError(
            "Dataset ANFIS no implementado. Target fisico PENDING VERIFICATION."
        )
