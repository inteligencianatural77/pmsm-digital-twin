"""M3 ELECTRICAL CORE reconstruido desde chart_33 de CloudE.

Responsabilidades:
- Clarke abc -> alpha-beta
- Park alpha-beta -> dq
- theta_e / omega_e
- Park inversa dq -> alpha-beta
- generacion de Va/Vb/Vc
- conversion a DUTY_A/B/C
- GATE_A/B/C
- ENABLE / FAULT
- Vs_mag

No implementa PWM carrier.
No implementa la planta PMSM.
"""

from __future__ import annotations

import math

from pmsm_hybrid_control.transforms.clarke import (
    clarke_transform,
    inverse_clarke_transform,
)
from pmsm_hybrid_control.transforms.park import (
    park_transform,
    inverse_park_transform,
    mechanical_to_electrical_angle,
)


class ElectricalCore:
    """Reconstrucción funcional del M3 electrical_core."""

    def __init__(self, pole_pairs: int = 4) -> None:
        self.pole_pairs = pole_pairs

    def step(
        self,
        *,
        id_ref: float,
        iq_ref: float,
        vd_in: float,
        vq_in: float,
        ia: float,
        ib: float,
        ic: float,
        theta_m: float,
        omega_m: float,
        vdc: float,
        enable_in: bool = True,
    ) -> dict[str, float | bool]:

        # ------------------------------------------------------------
        # Ángulo y velocidad eléctricos
        # ------------------------------------------------------------
        theta_e = mechanical_to_electrical_angle(
            theta_m,
            self.pole_pairs,
        )

        omega_e = self.pole_pairs * omega_m

        # ------------------------------------------------------------
        # Corrientes abc -> alpha-beta -> dq
        #
        # Equivale al M3:
        # i_alpha = ia
        # i_beta  = (ia + 2*ib) / sqrt(3)
        #
        # El transform existente usa:
        # i_beta = (ib - ic) / sqrt(3)
        #
        # Ambas son equivalentes si ia + ib + ic = 0.
        # ------------------------------------------------------------
        i_alpha, i_beta = clarke_transform(ia, ib, ic)

        id_, iq = park_transform(
            i_alpha,
            i_beta,
            theta_e,
        )

        # ------------------------------------------------------------
        # Tensiones dq
        # ------------------------------------------------------------
        vd = vd_in
        vq = vq_in

        # ------------------------------------------------------------
        # dq -> alpha-beta
        # ------------------------------------------------------------
        v_alpha, v_beta = inverse_park_transform(
            vd_in,
            vq_in,
            theta_e,
        )

        # ------------------------------------------------------------
        # alpha-beta -> abc
        # ------------------------------------------------------------
        va, vb, vc = inverse_clarke_transform(
            v_alpha,
            v_beta,
        )

        # ------------------------------------------------------------
        # M3 CloudE:
        #
        # DUTY_A = 0.5 + Va/VDC
        # DUTY_B = 0.5 + Vb/VDC
        # DUTY_C = 0.5 + Vc/VDC
        # ------------------------------------------------------------
        if vdc == 0:
            raise ValueError("VDC no puede ser cero en M3.")

        duty_a = 0.5 + va / vdc
        duty_b = 0.5 + vb / vdc
        duty_c = 0.5 + vc / vdc

        duty_a = max(0.0, min(1.0, duty_a))
        duty_b = max(0.0, min(1.0, duty_b))
        duty_c = max(0.0, min(1.0, duty_c))

        # ------------------------------------------------------------
        # GATE del M3 CloudE.
        # No es PWM carrier.
        # ------------------------------------------------------------
        gate_a = duty_a > 0.5
        gate_b = duty_b > 0.5
        gate_c = duty_c > 0.5

        enable = bool(enable_in)
        fault = False

        # ------------------------------------------------------------
        # Magnitud de tensión
        # ------------------------------------------------------------
        vs_mag = math.sqrt(vd_in * vd_in + vq_in * vq_in)

        limites_activos = (
            False,
            False,
            False,
            False,
        )

        return {
            "GATE_A": gate_a,
            "GATE_B": gate_b,
            "GATE_C": gate_c,
            "ENABLE": enable,
            "FAULT": fault,
            "DUTY_A": duty_a,
            "DUTY_B": duty_b,
            "DUTY_C": duty_c,
            "id": id_,
            "iq": iq,
            "Vd": vd,
            "Vq": vq,
            "omega_e": omega_e,
            "theta_e": theta_e,
            "VDC": vdc,
            "limites_activos": limites_activos,
            "Vs_mag": vs_mag,
        }
