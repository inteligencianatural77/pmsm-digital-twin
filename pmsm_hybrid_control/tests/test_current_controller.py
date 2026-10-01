from __future__ import annotations

import pytest

from pmsm_hybrid_control.foc.current_controller import CurrentController


KP = 15.0796
KI = 628.3185
DT = 50e-6


def make_controller(
    voltage_limit: float | None = None,
) -> CurrentController:
    return CurrentController(
        kp_id=KP,
        ki_id=KI,
        kp_iq=KP,
        ki_iq=KI,
        voltage_limit=voltage_limit,
    )


def test_zero_error_gives_zero_voltage() -> None:
    controller = make_controller()

    vd, vq = controller.update(
        id_ref=0.0,
        iq_ref=0.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    assert vd == 0.0
    assert vq == 0.0


def test_one_step_proportional_integral_response() -> None:
    controller = make_controller()

    vd, vq = controller.update(
        id_ref=1.0,
        iq_ref=2.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    expected_id = KP * 1.0 + KI * DT * 1.0
    expected_iq = KP * 2.0 + KI * DT * 2.0

    assert vd == pytest.approx(expected_id)
    assert vq == pytest.approx(expected_iq)


def test_integrator_accumulates_between_steps() -> None:
    controller = make_controller()

    vd1, vq1 = controller.update(
        id_ref=1.0,
        iq_ref=1.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    vd2, vq2 = controller.update(
        id_ref=1.0,
        iq_ref=1.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    expected_first = KP + KI * DT
    expected_second = KP + KI * (2.0 * DT)

    assert vd1 == pytest.approx(expected_first)
    assert vq1 == pytest.approx(expected_first)
    assert vd2 == pytest.approx(expected_second)
    assert vq2 == pytest.approx(expected_second)


def test_decoupling_terms_are_added_to_pi_output() -> None:
    controller = make_controller()

    vd, vq = controller.update(
        id_ref=0.0,
        iq_ref=0.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
        decoupling_d=12.0,
        decoupling_q=-7.0,
    )

    assert vd == pytest.approx(12.0)
    assert vq == pytest.approx(-7.0)


def test_voltage_limit_rolls_back_integrator() -> None:
    limit = 10.0
    controller = make_controller(voltage_limit=limit)

    vd, vq = controller.update(
        id_ref=10.0,
        iq_ref=0.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    # La salida proporcional + integral excede el límite.
    assert vd == pytest.approx(limit)
    assert vq == pytest.approx(0.0)

    # El rollback deja el integrador como estaba antes del paso.
    assert controller.int_id == pytest.approx(0.0)
    assert controller.int_iq == pytest.approx(0.0)


def test_reset_clears_integrators() -> None:
    controller = make_controller()

    controller.update(
        id_ref=1.0,
        iq_ref=1.0,
        id_meas=0.0,
        iq_meas=0.0,
        dt=DT,
    )

    controller.reset()

    assert controller.int_id == 0.0
    assert controller.int_iq == 0.0


@pytest.mark.parametrize("dt", [0.0, -1e-6])
def test_nonpositive_dt_is_rejected(dt: float) -> None:
    controller = make_controller()

    with pytest.raises(ValueError):
        controller.update(
            id_ref=0.0,
            iq_ref=0.0,
            id_meas=0.0,
            iq_meas=0.0,
            dt=dt,
        )
