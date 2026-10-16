import math

import pytest

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)


def make_model() -> StribeckFriction:
    return StribeckFriction(
        StribeckFrictionParameters(
            tc=0.5,
            ts=0.8,
            omega_s=10.0,
            delta=2.0,
            b=0.01,
        )
    )


def test_zero_speed_has_zero_friction_in_this_symmetric_model():
    model = make_model()

    assert model.torque(0.0) == pytest.approx(0.0)


def test_positive_speed_produces_positive_friction():
    model = make_model()

    assert model.torque(5.0) > 0.0


def test_negative_speed_produces_negative_friction():
    model = make_model()

    assert model.torque(-5.0) < 0.0


def test_friction_is_approximately_odd():
    model = make_model()

    positive = model.torque(7.0)
    negative = model.torque(-7.0)

    assert negative == pytest.approx(-positive)


def test_viscous_component_changes_with_speed():
    params = StribeckFrictionParameters(
        tc=0.0,
        ts=0.0,
        omega_s=1.0,
        delta=2.0,
        b=0.1,
    )

    model = StribeckFriction(params)

    assert model.torque(10.0) == pytest.approx(1.0)
    assert model.torque(-10.0) == pytest.approx(-1.0)


def test_parameters_are_validated():
    with pytest.raises(ValueError):
        StribeckFrictionParameters(
            tc=-1.0,
            ts=0.8,
            omega_s=10.0,
            delta=2.0,
            b=0.01,
        )

    with pytest.raises(ValueError):
        StribeckFrictionParameters(
            tc=0.8,
            ts=0.5,
            omega_s=10.0,
            delta=2.0,
            b=0.01,
        )

    with pytest.raises(ValueError):
        StribeckFrictionParameters(
            tc=0.5,
            ts=0.8,
            omega_s=0.0,
            delta=2.0,
            b=0.01,
        )


def test_nonfinite_speed_is_rejected():
    model = make_model()

    with pytest.raises(ValueError):
        model.torque(math.nan)

    with pytest.raises(ValueError):
        model.torque(math.inf)
