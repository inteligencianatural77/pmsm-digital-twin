"""B0.1 — Ensayo de lazo de corriente Iq.

Baseline histórico M6 sobre planta M4_BASE.

NO modifica los módulos de producción.
Las ganancias del PI son las históricas de la referencia M6.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.foc_reconstructed.current_controller import CurrentController
from pmsm_hybrid_control.foc_reconstructed.decoupling import Decoupling
from pmsm_hybrid_control.transforms.clarke import clarke_transform
from pmsm_hybrid_control.transforms.park import (
    inverse_park_transform,
    mechanical_to_electrical_angle,
    park_transform,
)


# ---------------------------------------------------------------------
# Experimento
# ---------------------------------------------------------------------

DT = 50e-6
T_END = 0.050

STEP_TIME = 0.001
IQ_STEP = 10.0
ID_REF = 0.0

# Condición de bus usada por la referencia histórica.
VDC = 600.0

# Ganancias históricas M6.
KP_ID = 15.0796
KI_ID = 628.3185
KP_IQ = 15.0796
KI_IQ = 628.3185


def main() -> None:
    plant = PMSMBase()

    controller = CurrentController(
        kp_id=KP_ID,
        ki_id=KI_ID,
        kp_iq=KP_IQ,
        ki_iq=KI_IQ,
    )

    decoupling = Decoupling()

    # Estados iniciales de la realimentación.
    theta_m = 0.0
    omega_m = 0.0
    ia = 0.0
    ib = 0.0
    ic = 0.0

    rows: list[dict[str, float]] = []

    n_steps = int(round(T_END / DT))

    for k in range(n_steps + 1):
        t = k * DT

        # Medición abc -> dq.
        i_alpha, i_beta = clarke_transform(ia, ib, ic)
        theta_e = mechanical_to_electrical_angle(
            theta_m,
            plant.params.n_pole_pairs,
        )
        id_meas, iq_meas = park_transform(
            i_alpha,
            i_beta,
            theta_e,
        )

        # Escalón de referencia.
        iq_ref = IQ_STEP if t >= STEP_TIME else 0.0

        # Desacoplamiento usando el estado actual.
        omega_e = plant.params.n_pole_pairs * omega_m

        vd_dec, vq_dec = decoupling.apply(
            id_=id_meas,
            iq=iq_meas,
            omega_e=omega_e,
            ld=plant.params.ld,
            lq=plant.params.lq,
            lambda_m=0.1100,  # referencia histórica M6
        )

        v_max = 0.95 * VDC / math.sqrt(3.0)
        controller.voltage_limit = v_max

        vd, vq = controller.update(
            id_ref=ID_REF,
            iq_ref=iq_ref,
            id_meas=id_meas,
            iq_meas=iq_meas,
            dt=DT,
            decoupling_d=vd_dec,
            decoupling_q=vq_dec,
        )

        # dq -> abc.
        v_alpha, v_beta = inverse_park_transform(
            vd,
            vq,
            theta_e,
        )

        va = v_alpha
        vb = -0.5 * v_alpha + 0.5 * math.sqrt(3.0) * v_beta
        vc = -0.5 * v_alpha - 0.5 * math.sqrt(3.0) * v_beta

        # Planta M4.
        out = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=0.0,
                theta_m=theta_m,
            ),
            DT,
        )

        ia = out.ia
        ib = out.ib
        ic = out.ic
        omega_m = out.omega_m
        theta_m = out.theta_m

        v_dq = math.sqrt(vd * vd + vq * vq)

        rows.append(
            {
                "t": t,
                "id_ref": ID_REF,
                "id": id_meas,
                "iq_ref": iq_ref,
                "iq": iq_meas,
                "vd": vd,
                "vq": vq,
                "v_dq": v_dq,
                "v_max": v_max,
                "te": out.te,
                "omega_m": omega_m,
                "theta_m": theta_m,
                "theta_e": theta_e,
                "ia": ia,
                "ib": ib,
                "ic": ic,
            }
        )

    output = Path("experiments/b0_1_current_iq_step.csv")

    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("========================================")
    print(" B0.1 — CURRENT IQ STEP")
    print("========================================")
    print(f"dt       = {DT} s")
    print(f"duration = {T_END} s")
    print(f"step     = {STEP_TIME} s")
    print(f"Iq_ref   = {IQ_STEP} A")
    print(f"Kp_i     = {KP_IQ}")
    print(f"Ki_i     = {KI_IQ}")
    print(f"Vdc      = {VDC} V")
    print(f"Vmax     = {v_max:.6f} V")
    print(f"samples  = {len(rows)}")
    print(f"output   = {output}")
    print()
    print(f"final id = {rows[-1]['id']:.6f} A")
    print(f"final iq = {rows[-1]['iq']:.6f} A")
    print(f"final Te = {rows[-1]['te']:.6f} N*m")
    print(f"final wm = {rows[-1]['omega_m']:.6f} rad/s")


if __name__ == "__main__":
    main()
