from __future__ import annotations

import numpy as np
import pytest

from pmsm_hybrid_control.foc.foc import FOC


DT = 50e-6

LD = 0.0012
LQ = 0.0012
LAMBDA_M = 0.107245
POLE_PAIRS = 4


def test_zero_current_reference_and_zero_current_measurement() -> None:
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=0.0,
        id_ref=0.0,
        iq_ref=0.0,
        dt=DT,
    )

    assert va == pytest.approx(0.0)
    assert vb == pytest.approx(0.0)
    assert vc == pytest.approx(0.0)


def test_current_error_produces_three_phase_voltage() -> None:
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=0.0,
        id_ref=0.0,
        iq_ref=10.0,
        dt=DT,
    )

    # theta_e = 0:
    # vd = 0, vq > 0
    # inverse Park -> alpha = 0, beta = vq
    # inverse Clarke -> va=0,
    #                   vb=+sqrt(3)/2*vq,
    #                   vc=-sqrt(3)/2*vq
    assert va == pytest.approx(0.0)
    assert vb > 0.0
    assert vc < 0.0
    assert va + vb + vc == pytest.approx(0.0)


def test_positive_electrical_speed_adds_decoupling() -> None:
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=10.0,
        id_ref=0.0,
        iq_ref=0.0,
        dt=DT,
    )

    omega_e = POLE_PAIRS * 10.0
    expected_vq = omega_e * LAMBDA_M

    assert va == pytest.approx(0.0)
    assert vb == pytest.approx(np.sqrt(3.0) / 2.0 * expected_vq)
    assert vc == pytest.approx(-np.sqrt(3.0) / 2.0 * expected_vq)
    assert va + vb + vc == pytest.approx(0.0)


def test_mechanical_angle_changes_electrical_orientation() -> None:
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )

    theta_m = 0.1
    theta_e = POLE_PAIRS * theta_m

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=theta_m,
        omega_m=0.0,
        id_ref=0.0,
        iq_ref=10.0,
        dt=DT,
    )

    # Con referencia puramente q:
    # alpha = -vq*sin(theta_e)
    # beta  =  vq*cos(theta_e)
    # va = alpha
    assert va < 0.0

    assert va + vb + vc == pytest.approx(0.0)


def test_invalid_dt_is_rejected() -> None:
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )

    with pytest.raises(ValueError):
        foc.step(
            ia=0.0,
            ib=0.0,
            ic=0.0,
            theta_m=0.0,
            omega_m=0.0,
            id_ref=0.0,
            iq_ref=0.0,
            dt=0.0,
        )


def test_voltage_vector_is_limited_after_decoupling() -> None:
    limit = 10.0
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
        voltage_limit=limit,
    )

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=100.0,
        id_ref=0.0,
        iq_ref=10.0,
        dt=DT,
    )

    # La transformación inversa de Clarke usada por el proyecto
    # conserva la magnitud del vector en alfa-beta.
    v_alpha = va
    v_beta = (vb - vc) / 3**0.5
    magnitude = (v_alpha**2 + v_beta**2) ** 0.5

    assert magnitude <= limit + 1e-9


def test_vector_saturation_preserves_voltage_direction() -> None:
    limit = 10.0
    foc = FOC(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
        voltage_limit=limit,
    )

    va, vb, vc = foc.step(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=100.0,
        id_ref=0.0,
        iq_ref=0.0,
        dt=DT,
    )

    assert va == pytest.approx(0.0, abs=1e-9)
    assert vb == pytest.approx(-vc, abs=1e-9)
    assert (va**2 + vb**2 + vc**2) > 0.0


def test_nonpositive_voltage_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        FOC(
            ld=LD,
            lq=LQ,
            lambda_m=LAMBDA_M,
            pole_pairs=POLE_PAIRS,
            voltage_limit=0.0,
        )


def test_vector_saturation_preserves_direction_and_limits_magnitude() -> None:
    limit = 10.0
    kwargs = dict(
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
        pole_pairs=POLE_PAIRS,
    )
    foc_unlimited = FOC(**kwargs)
    foc_limited = FOC(**kwargs, voltage_limit=limit)

    inputs = dict(
        ia=0.0,
        ib=0.0,
        ic=0.0,
        theta_m=0.0,
        omega_m=100.0,
        id_ref=0.0,
        iq_ref=10.0,
        dt=DT,
    )

    phases_unlimited = foc_unlimited.step(**inputs)
    phases_limited = foc_limited.step(**inputs)

    def alpha_beta(phases: tuple[float, float, float]) -> np.ndarray:
        va, vb, vc = phases
        return np.asarray([va, (vb - vc) / np.sqrt(3.0)])

    vector_unlimited = alpha_beta(phases_unlimited)
    vector_limited = alpha_beta(phases_limited)

    mag_unlimited = np.linalg.norm(vector_unlimited)
    mag_limited = np.linalg.norm(vector_limited)

    assert mag_unlimited > limit
    assert mag_limited == pytest.approx(limit, abs=1e-8)

    scale = limit / mag_unlimited
    assert vector_limited == pytest.approx(
        vector_unlimited * scale,
        abs=1e-8,
    )
