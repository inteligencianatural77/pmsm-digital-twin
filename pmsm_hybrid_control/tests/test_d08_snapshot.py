"""D-08 (opcion A): PlantOutput como instantanea coherente de x[k+1].

Hipotesis contractual:
    Park(Clarke(ia, ib, ic), p*theta_m_out) == (id, iq)

El test NO modifica la planta.
"""

import math

import pytest

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.transforms.clarke import clarke_transform
from pmsm_hybrid_control.transforms.park import park_transform


DT = 50e-6

OMEGAS = [
    0.0,
    68.773872,
    309.218699,
    696.0,
    1385.0,
    -309.218699,
]


def _plant_at(
    omega_m,
    id_=-0.6,
    iq=10.0,
    theta_m=1.234,
):
    plant = PMSMBase()
    plant._id = id_
    plant._iq = iq
    plant._omega_m = omega_m
    plant._theta_m = theta_m
    return plant


def _inp(
    va=3.0,
    vb=-1.0,
    vc=-2.0,
    t_load=0.5,
):
    return PlantInput(
        va=va,
        vb=vb,
        vc=vc,
        t_load=t_load,
    )


@pytest.mark.parametrize("omega_m", OMEGAS)
def test_snapshot_invariant(omega_m):
    plant = _plant_at(omega_m)

    out = plant.step(
        _inp(),
        DT,
    )

    p = plant.params.n_pole_pairs

    i_alpha, i_beta = clarke_transform(
        out.ia,
        out.ib,
        out.ic,
    )

    id_seen, iq_seen = park_transform(
        i_alpha,
        i_beta,
        p * out.theta_m,
    )

    assert id_seen == pytest.approx(
        out.id,
        abs=1e-9,
    )
    assert iq_seen == pytest.approx(
        out.iq,
        abs=1e-9,
    )


def test_snapshot_invariant_multistep_closed_loop_like():
    plant = _plant_at(500.0)

    p = plant.params.n_pole_pairs

    for k in range(200):
        out = plant.step(
            _inp(
                va=5 * math.sin(k * 0.01),
                vb=-2.0,
                vc=2.0 - 5 * math.sin(k * 0.01),
            ),
            DT,
        )

        i_alpha, i_beta = clarke_transform(
            out.ia,
            out.ib,
            out.ic,
        )

        id_seen, iq_seen = park_transform(
            i_alpha,
            i_beta,
            p * out.theta_m,
        )

        assert id_seen == pytest.approx(
            out.id,
            abs=1e-9,
        )
        assert iq_seen == pytest.approx(
            out.iq,
            abs=1e-9,
        )


def test_omega_zero_theta_unchanged_and_abc_matches_input_angle():
    from pmsm_hybrid_control.transforms.park import inverse_park_transform
    from pmsm_hybrid_control.transforms.clarke import inverse_clarke_transform

    plant = _plant_at(0.0)

    theta_in = plant.states["theta_m"]

    out = plant.step(
        _inp(),
        DT,
    )

    assert out.theta_m == theta_in

    p = plant.params.n_pole_pairs

    ref = inverse_clarke_transform(
        *inverse_park_transform(
            out.id,
            out.iq,
            p * theta_in,
        )
    )

    assert (out.ia, out.ib, out.ic) == pytest.approx(
        ref,
        abs=1e-12,
    )


def test_dynamics_unchanged_euler_reference():
    plant = _plant_at(309.218699)

    p = plant.params.n_pole_pairs
    prm = plant.params

    inp = _inp()

    id0 = plant.states["id"]
    iq0 = plant.states["iq"]
    w0 = plant.states["omega_m"]
    th0 = plant.states["theta_m"]

    i_alpha = inp.va
    i_beta = (inp.vb - inp.vc) / math.sqrt(3.0)

    c = math.cos(p * th0)
    s = math.sin(p * th0)

    vd = i_alpha * c + i_beta * s
    vq = -i_alpha * s + i_beta * c

    we = p * w0

    te = (
        1.5
        * p
        * (
            prm.lambda_m * iq0
            + (prm.ld - prm.lq) * id0 * iq0
        )
    )

    expected = (
        id0 + DT * (
            vd
            - prm.rs * id0
            + we * prm.lq * iq0
        ) / prm.ld,

        iq0 + DT * (
            vq
            - prm.rs * iq0
            - we * (prm.ld * id0 + prm.lambda_m)
        ) / prm.lq,

        w0 + DT * (te - inp.t_load) / prm.j,

        th0 + DT * w0,
    )

    out = plant.step(inp, DT)

    assert (
        out.id,
        out.iq,
        out.omega_m,
        out.theta_m,
    ) == pytest.approx(
        expected,
        rel=1e-12,
        abs=1e-12,
    )
