"""Tests de consistencia de software del M4_BASE (NO validacion fisica)."""
import math
import pytest
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput, PlantOutput


def test_construction_and_initial_states():
    plant = PMSMBase()
    s = plant.states
    assert s == {"id": 0.0, "iq": 0.0, "omega_m": 0.0, "theta_m": 0.0}


def test_torque_reference_equation():
    plant = PMSMBase()
    # Te = (3/2)*p*(lambda_m*iq + (Ld-Lq)*id*iq); con Ld=Lq e iq=2A
    te = plant.electromagnetic_torque(id_=1.0, iq=2.0)
    assert te == pytest.approx(1.5 * 4 * 0.107245 * 2.0, abs=1e-12)


def test_theta_e_is_four_times_theta_m():
    plant = PMSMBase()
    plant.step(PlantInput(theta_m=0.25, va=0, vb=0, vc=0, t_load=0), 1e-6)
    assert plant.theta_e == pytest.approx(4 * plant.states["theta_m"])


def test_interface_io_contract():
    plant = PMSMBase()
    out = plant.step(PlantInput(va=1.0, vb=-0.5, vc=-0.5, t_load=0.1,
                                theta_m=0.0), 50e-6)
    assert isinstance(out, PlantOutput)
    assert out.ia + out.ib + out.ic == pytest.approx(0.0, abs=1e-9)


def test_simulation_runs_without_blowup():
    plant = PMSMBase()
    out = None
    for k in range(200):
        t = k * 50e-6
        out = plant.step(PlantInput(
            va=5*math.sin(2*math.pi*50*t),
            vb=5*math.sin(2*math.pi*50*t - 2*math.pi/3),
            vc=5*math.sin(2*math.pi*50*t + 2*math.pi/3),
            t_load=0.0, theta_m=plant.states["theta_m"]), 50e-6)
    assert all(math.isfinite(v) for v in [out.ia, out.ib, out.ic, out.omega_m, out.te])


def test_zero_input_zero_state():
    plant = PMSMBase()
    out = plant.step(PlantInput(), 50e-6)
    assert out.ia == pytest.approx(0.0, abs=1e-12)
    assert out.te == pytest.approx(0.0, abs=1e-12)
