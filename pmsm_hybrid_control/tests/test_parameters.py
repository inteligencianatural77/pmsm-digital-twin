"""Tests de parametros M4: valores CONFIRMED exactos vs especificacion."""
import math
from pmsm_hybrid_control.plant.parameters import (
    default_m4_parameters, TraceStatus, LAMBDA_M, B_PENDING, TFRIC_PENDING,
)


def test_confirmed_electrical_values():
    p = default_m4_parameters()
    assert p.rs == 0.05            # CONFIRMED 01_M4_HARD_DATA.md#2
    assert p.ms == 0.00002
    assert p.l0 == 0.00016
    assert p.ld == 0.0012
    assert p.lq == 0.0012


def test_lambda_m_is_m4_value_not_cloude():
    # Regla critica: M4 lambda_m = 0.107245, NUNCA el de CloudE (0.11)
    assert LAMBDA_M.value == 0.107245
    assert LAMBDA_M.value != 0.11
    assert LAMBDA_M.status == TraceStatus.CONFIRMED


def test_electromechanical_values():
    p = default_m4_parameters()
    assert p.n == 6                # N del bloque; NO es numero de pares de polos
    assert p.n_pole_pairs == 4     # 8 polos fisicos
    assert p.j == 0.00416


def test_pending_parameters_not_invented():
    assert B_PENDING.status == TraceStatus.PENDING_VERIFICATION
    assert TFRIC_PENDING.status == TraceStatus.PENDING_VERIFICATION
    assert math.isnan(B_PENDING.value)
    assert math.isnan(TFRIC_PENDING.value)
    p = default_m4_parameters()
    assert set(p.pending_parameters.keys()) == {"B", "Tfric"}
