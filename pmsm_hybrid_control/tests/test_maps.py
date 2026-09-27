"""Tests Phase 2 — MAPAS (base analitica PROPOSED + tablas recuperadas PENDING)."""
import numpy as np
import pytest
from pmsm_hybrid_control.plant.flux_maps import FluxMap, recovered_m4_tables, RecoveredTable
from pmsm_hybrid_control.plant.torque_map import TorqueMap
from pmsm_hybrid_control.plant.parameters import TraceStatus


def test_flux_map_analytic_from_confirmed_params():
    m = FluxMap()
    # psi_d = Ld*id + lambda_m ; psi_q = Lq*iq  (Ld=Lq=1.2e-3, lambda_m=0.107245)
    psi_d, psi_q = m.evaluate(id_a=10.0, iq=5.0)
    assert psi_d == pytest.approx(0.0012 * 10.0 + 0.107245, abs=1e-12)
    assert psi_q == pytest.approx(0.0012 * 5.0, abs=1e-12)


def test_flux_map_independent_of_theta_and_position():
    # constantMutualInductance: sin variacion con posicion (CONFIRMED parametrizacion)
    m = FluxMap()
    assert m.evaluate(3.0, 2.0, 0.0) == m.evaluate(3.0, 2.0, 1.7)


def test_flux_map_rejects_recovered_tables_pending():
    with pytest.raises(NotImplementedError):
        FluxMap(use_recovered_tables=True)
    with pytest.raises(NotImplementedError):
        TorqueMap(use_recovered_tables=True)


def test_torque_map_matches_reference_equation():
    t = TorqueMap()
    # Ld = Lq -> termino de saliencia nulo
    assert t.evaluate(id_a=8.0, iq=3.0) == pytest.approx(1.5 * 4 * 0.107245 * 3.0, abs=1e-12)
    assert t.evaluate(id_a=0.0, iq=0.0) == 0.0


def test_recovered_tables_are_pending_not_active():
    tables = recovered_m4_tables()
    assert "dfluxdiMatrix" in tables and "LdMatrix" in tables and "fluxD_dq0" in tables
    for name, tab in tables.items():
        assert isinstance(tab, RecoveredTable)
        assert tab.status == TraceStatus.PENDING_VERIFICATION  # ninguna es activa


def test_recovered_table_values_match_hard_data():
    tables = recovered_m4_tables()
    assert np.allclose(tables["dfluxdiMatrix"].data, 0.0002 * np.ones((3, 4)))
    assert np.allclose(tables["LdMatrix"].data, 1.2e-3 * np.ones((3, 3)))
    assert tables["LdMatrix"].data.shape == (3, 3)
    assert tables["fluxD_dq0"].data.shape == (3, 3, 7)
