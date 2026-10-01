from __future__ import annotations

import pytest

from pmsm_hybrid_control.foc.current_controller import CurrentController
from pmsm_hybrid_control.foc.decoupling import Decoupling


KP = 15.0796
KI = 628.3185

LD = 0.0012
LQ = 0.0012
LAMBDA_M = 0.107245

DT = 50e-6


def test_pi_output_is_composed_with_decoupling_once() -> None:
    controller = CurrentController(
        kp_id=KP,
        ki_id=KI,
        kp_iq=KP,
        ki_iq=KI,
    )
    decoupling = Decoupling()

    id_ref = 10.0
    iq_ref = 20.0
    id_meas = 2.0
    iq_meas = 5.0
    omega_e = 100.0

    vd_pi, vq_pi = controller.update(
        id_ref=id_ref,
        iq_ref=iq_ref,
        id_meas=id_meas,
        iq_meas=iq_meas,
        dt=DT,
    )

    vd, vq = decoupling.apply(
        vd_pi=vd_pi,
        vq_pi=vq_pi,
        id_=id_meas,
        iq=iq_meas,
        omega_e=omega_e,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    int_id = (id_ref - id_meas) * DT
    int_iq = (iq_ref - iq_meas) * DT

    expected_vd_pi = KP * (id_ref - id_meas) + KI * int_id
    expected_vq_pi = KP * (iq_ref - iq_meas) + KI * int_iq

    expected_vd = expected_vd_pi - omega_e * LQ * iq_meas
    expected_vq = expected_vq_pi + omega_e * (
        LD * id_meas + LAMBDA_M
    )

    assert vd_pi == pytest.approx(expected_vd_pi)
    assert vq_pi == pytest.approx(expected_vq_pi)
    assert vd == pytest.approx(expected_vd)
    assert vq == pytest.approx(expected_vq)


def test_zero_speed_composition_reduces_to_pi_output() -> None:
    controller = CurrentController()
    decoupling = Decoupling()

    vd_pi, vq_pi = controller.update(
        id_ref=5.0,
        iq_ref=7.0,
        id_meas=1.0,
        iq_meas=2.0,
        dt=DT,
    )

    vd, vq = decoupling.apply(
        vd_pi=vd_pi,
        vq_pi=vq_pi,
        id_=1.0,
        iq=2.0,
        omega_e=0.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    assert vd == pytest.approx(vd_pi)
    assert vq == pytest.approx(vq_pi)


def test_current_controller_without_decoupling_preserves_integrator_state() -> None:
    controller = CurrentController()

    controller.update(
        id_ref=10.0,
        iq_ref=20.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    expected_int_id = 10.0 * DT
    expected_int_iq = 20.0 * DT

    assert controller.int_id == pytest.approx(expected_int_id)
    assert controller.int_iq == pytest.approx(expected_int_iq)


def test_composition_does_not_use_historical_lambda_m() -> None:
    controller = CurrentController()
    decoupling = Decoupling()

    vd_pi, vq_pi = controller.update(
        id_ref=0.0,
        iq_ref=0.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    _, vq = decoupling.apply(
        vd_pi=vd_pi,
        vq_pi=vq_pi,
        id_=0.0,
        iq=0.0,
        omega_e=100.0,
        ld=LD,
        lq=LQ,
        lambda_m=LAMBDA_M,
    )

    assert vq == pytest.approx(100.0 * LAMBDA_M)
    assert vq != pytest.approx(100.0 * 0.1100)
