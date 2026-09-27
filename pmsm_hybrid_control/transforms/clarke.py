"""Transformada de Clarke y su inversa.

Convencion: invariante en amplitud (amplitude-invariant), asumida con
i_a + i_b + i_c = 0 (conexion wye con puerto neutral no expuesto — CONFIRMED).

ESTADO: la eleccion 'invariante en amplitud' es PROPOSED como decision de
implementacion consistente con la convencion Park confirmada
(QleadsD_AphaseToDaxis), de modo que la amplitud de fase se conserva en
el plano alfa-beta. No cambiar signos sin documentarlo (MASTER_SPEC #21).
"""
from __future__ import annotations

import numpy as np

SQRT3 = np.sqrt(3.0)


def clarke_transform(ia: float, ib: float, ic: float) -> tuple[float, float]:
    """abc -> alfa-beta (invariante en amplitud).

    i_alpha = ia
    i_beta  = (ib - ic) / sqrt(3)

    Valida i_a+i_b+i_c ~= 0 (tolerancia numerica interna, NO de validacion fisica).
    """
    if abs(ia + ib + ic) > 1e-9:
        raise ValueError("Clarke asume i_a+i_b+i_c=0 (wye, neutral no expuesto)")
    i_alpha = ia
    i_beta = (ib - ic) / SQRT3
    return float(i_alpha), float(i_beta)


def inverse_clarke_transform(i_alpha: float, i_beta: float) -> tuple[float, float, float]:
    """alfa-beta -> abc (invariante en amplitud)."""
    i_a = i_alpha
    i_b = -0.5 * i_alpha + 0.5 * SQRT3 * i_beta
    i_c = -0.5 * i_alpha - 0.5 * SQRT3 * i_beta
    return float(i_a), float(i_b), float(i_c)
