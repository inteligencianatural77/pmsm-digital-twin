"""FOC COMPLETO — PHASE 5 (NO IMPLEMENTADO).

Contrato conceptual FOC <-> planta (MASTER_SPEC #24):
entradas ia/ib/ic, theta, omega, id_ref, iq_ref; salidas va/vb/vc.
Unidades, signos, convencion, frecuencia de muestreo y limites:
PENDING VERIFICATION.

ESTADO: PENDING — interfaz placeholder unicamente.
"""
from __future__ import annotations


class FOCNotImplementedError(NotImplementedError):
    pass


class FOC:
    """Interfaz placeholder del lazo FOC completo."""

    def step(self, ia: float, ib: float, ic: float, theta_m: float,
             omega_m: float, id_ref: float, iq_ref: float, dt: float):
        raise FOCNotImplementedError(
            "FOC no implementado. Se construira tras M4_NONLINEAR (orden oficial)."
        )
