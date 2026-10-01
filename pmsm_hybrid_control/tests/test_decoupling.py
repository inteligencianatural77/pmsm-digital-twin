from __future__ import annotations

import pytest

from pmsm_hybrid_control.foc.decoupling import Decoupling


LD = 0.0012
LQ = 0.0012
LAMBDA_M = 0.107245


def test_zero_speed_preserves_pi_voltage() -> None:
    vd, vq = Decoupling().apply(
        vd_pi=10.0,
        vq_pi=20.0,
        id_=5.0,
        iq=7.0,
        omega_e=0.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    assert vd == pytest.approx(10.0)
    assert vq == pytest.approx(20.0)


def test_d_axis_decoupling_term() -> None:
    vd, vq = Decoupling().apply(
        vd_pi=0.0,
        vq_pi=0.0,
        id_=0.0,
        iq=10.0,
        omega_e=100.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    expected_vd = -100.0 * LQ * 10.0

    assert vd == pytest.approx(expected_vd)
    assert vq == pytest.approx(100.0 * LAMBDA_M)


def test_q_axis_decoupling_includes_id_and_magnet_flux() -> None:
    vd, vq = Decoupling().apply(
        vd_pi=0.0,
        vq_pi=0.0,
        id_=20.0,
        iq=0.0,
        omega_e=50.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    expected_vd = 0.0
    expected_vq = 50.0 * (LD * 20.0 + LAMBDA_M)

    assert vd == pytest.approx(expected_vd)
    assert vq == pytest.approx(expected_vq)


def test_pi_voltage_is_added_to_decoupling_terms() -> None:
    vd, vq = Decoupling().apply(
        vd_pi=3.0,
        vq_pi=-4.0,
        id_=2.0,
        iq=5.0,
        omega_e=80.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    expected_vd = 3.0 - 80.0 * LQ * 5.0
    expected_vq = -4.0 + 80.0 * (LD * 2.0 + LAMBDA_M)

    assert vd == pytest.approx(expected_vd)
    assert vq == pytest.approx(expected_vq)


def test_m4_lambda_m_is_used_without_historical_0110_override() -> None:
    _, vq = Decoupling().apply(
        vd_pi=0.0,
        vq_pi=0.0,
        id_=0.0,
        iq=0.0,
        omega_e=100.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    assert vq == pytest.approx(100.0 * LAMBDA_M)
    assert vq != pytest.approx(100.0 * 0.1100)
