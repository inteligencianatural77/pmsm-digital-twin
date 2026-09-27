"""Transformada de Park y su inversa.

CONVENCION CONFIRMADA M4: QleadsD_AphaseToDaxis
(01_M4_HARD_DATA.md#20; 02_CONTRACTS.md#3.1).
- La fase A queda alineada con el eje d cuando theta_e = 0.
- El eje q adelanta al eje d.
- theta_e = n_pole_pairs * theta_m = 4 * theta_m (rad).

NO sustituir por otra convencion Park sin documentar la transformacion.
"""
from __future__ import annotations

import numpy as np


def park_transform(i_alpha: float, i_beta: float, theta_e: float) -> tuple[float, float]:
    """alfa-beta -> dq. A-phase alineada al eje d en theta_e = 0.

    id =  i_alpha*cos(theta_e) + i_beta*sin(theta_e)
    iq = -i_alpha*sin(theta_e) + i_beta*cos(theta_e)
    """
    c = np.cos(theta_e)
    s = np.sin(theta_e)
    i_d = i_alpha * c + i_beta * s
    i_q = -i_alpha * s + i_beta * c
    return float(i_d), float(i_q)


def inverse_park_transform(i_d: float, i_q: float, theta_e: float) -> tuple[float, float]:
    """dq -> alfa-beta (inversa exacta de park_transform)."""
    c = np.cos(theta_e)
    s = np.sin(theta_e)
    i_alpha = i_d * c - i_q * s
    i_beta = i_d * s + i_q * c
    return float(i_alpha), float(i_beta)


def mechanical_to_electrical_angle(theta_m: float, n_pole_pairs: int = 4) -> float:
    """theta_e = p * theta_m (p=4 CONFIRMED). Unico lugar del codigo con esta conversion."""
    return n_pole_pairs * theta_m


def electrical_to_mechanical_angle(theta_e: float, n_pole_pairs: int = 4) -> float:
    """theta_m = theta_e / p."""
    return theta_e / n_pole_pairs
