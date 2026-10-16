import math

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.plant.pmsm_with_friction import PMSMWithFriction


def _zero_input():
    return PlantInput(
        va=0.0,
        vb=0.0,
        vc=0.0,
        t_load=0.0,
    )


def _scenario_input():
    return PlantInput(
        va=10.0,
        vb=-5.0,
        vc=-5.0,
        t_load=0.0,
    )


def test_without_friction_matches_pmsm_base():
    """Sin fricción, la variante debe reproducir PMSMBase."""
    base = PMSMBase()
    variant = PMSMWithFriction(friction=None)

    dt = 50e-6

    for _ in range(100):
        out_base = base.step(_scenario_input(), dt)
        out_variant = variant.step(_scenario_input(), dt)

        assert math.isclose(
            out_variant.id,
            out_base.id,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

        assert math.isclose(
            out_variant.iq,
            out_base.iq,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

        assert math.isclose(
            out_variant.omega_m,
            out_base.omega_m,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

        assert math.isclose(
            out_variant.theta_m,
            out_base.theta_m,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

        assert math.isclose(
            out_variant.te,
            out_base.te,
            rel_tol=0.0,
            abs_tol=1e-12,
        )


def test_zero_friction_parameters_match_base():
    """Una ley de fricción nula debe dejar la dinámica equivalente."""
    params = StribeckFrictionParameters(
        tc=0.0,
        ts=0.0,
        omega_s=10.0,
        delta=2.0,
        b=0.0,
    )

    friction = StribeckFriction(params)

    base = PMSMBase()
    variant = PMSMWithFriction(friction=friction)

    dt = 50e-6

    for _ in range(100):
        out_base = base.step(_scenario_input(), dt)
        out_variant = variant.step(_scenario_input(), dt)

        assert math.isclose(
            out_variant.omega_m,
            out_base.omega_m,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

        assert math.isclose(
            out_variant.theta_m,
            out_base.theta_m,
            rel_tol=0.0,
            abs_tol=1e-12,
        )


def test_friction_reduces_positive_acceleration():
    """Con velocidad positiva, la fricción reduce la aceleración mecánica."""
    params = StribeckFrictionParameters(
        tc=0.5,
        ts=0.8,
        omega_s=10.0,
        delta=2.0,
        b=0.01,
    )

    friction = StribeckFriction(params)

    base = PMSMBase()
    variant = PMSMWithFriction(friction=friction)

    # Establecer explícitamente un estado mecánico positivo para la prueba.
    base._omega_m = 10.0
    variant._omega_m = 10.0

    # La variante debe introducir exactamente el par de fricción esperado.
    expected_tf = friction.torque(10.0)

    assert math.isclose(
        variant.friction_torque(),
        expected_tf,
        rel_tol=0.0,
        abs_tol=1e-15,
    )

    # Con los mismos estados y entradas, la derivada mecánica de la variante
    # debe ser menor por exactamente Tf/J.
    inp = _zero_input()

    omega_e = base.params.n_pole_pairs * base._omega_m

    base_derivatives = base._derivatives(
        0.0,
        0.0,
        inp.t_load,
        omega_e,
    )

    variant_derivatives = variant._derivatives(
        0.0,
        0.0,
        inp.t_load,
        omega_e,
    )

    expected_difference = expected_tf / base.params.j

    assert math.isclose(
        base_derivatives[2] - variant_derivatives[2],
        expected_difference,
        rel_tol=0.0,
        abs_tol=1e-12,
    )

    assert variant_derivatives[2] < base_derivatives[2]

def test_friction_torque_is_exposed():
    params = StribeckFrictionParameters(
        tc=0.5,
        ts=0.8,
        omega_s=10.0,
        delta=2.0,
        b=0.01,
    )

    friction = StribeckFriction(params)
    variant = PMSMWithFriction(friction=friction)

    assert math.isclose(
        variant.friction_torque(),
        0.0,
        rel_tol=0.0,
        abs_tol=1e-15,
    )
