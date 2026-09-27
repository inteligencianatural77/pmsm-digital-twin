"""Tests de Clarke/Park y conversion de angulos."""
import pytest
from pmsm_hybrid_control.transforms.clarke import clarke_transform, inverse_clarke_transform
from pmsm_hybrid_control.transforms.park import (
    park_transform, inverse_park_transform,
    mechanical_to_electrical_angle, electrical_to_mechanical_angle,
)


def test_clarke_inverse_roundtrip():
    ia, ib, ic = 3.0, -1.5, -1.5   # suma cero (wye)
    a, b = clarke_transform(ia, ib, ic)
    ra, rb, rc = inverse_clarke_transform(a, b)
    assert ra == pytest.approx(ia, abs=1e-12)
    assert rb == pytest.approx(ib, abs=1e-12)
    assert rc == pytest.approx(ic, abs=1e-12)


def test_clarke_rejects_unbalanced():
    with pytest.raises(ValueError):
        clarke_transform(1.0, 1.0, 1.0)


def test_park_convention_qleadsd_aphase_to_daxis():
    # En theta_e = 0 la fase A debe caer enteramente en el eje d (CONFIRMED)
    i_d, i_q = park_transform(5.0, 0.0, 0.0)
    assert i_d == pytest.approx(5.0, abs=1e-12)
    assert i_q == pytest.approx(0.0, abs=1e-12)


def test_park_inverse_roundtrip():
    a, b = 2.0, -3.0
    d, q = park_transform(a, b, 0.7)
    ra, rb = inverse_park_transform(d, q, 0.7)
    assert ra == pytest.approx(a, abs=1e-12)
    assert rb == pytest.approx(b, abs=1e-12)


def test_pole_pairs_angle_relation():
    assert mechanical_to_electrical_angle(0.5) == pytest.approx(2.0)   # 4 * 0.5
    assert electrical_to_mechanical_angle(2.0) == pytest.approx(0.5)
    assert mechanical_to_electrical_angle(
        electrical_to_mechanical_angle(1.234)) == pytest.approx(1.234)
