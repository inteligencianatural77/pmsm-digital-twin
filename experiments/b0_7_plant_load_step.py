"""
B0.7 — RESPUESTA DE LA PLANTA ANTE ESCALÓN DE TORQUE DE CARGA

Ensayo de desarrollo de PMSMBase sin controlador FOC.

Objetivo:
    Caracterizar la respuesta de la planta M4_BASE ante la aplicación
    de un torque de carga durante la operación.

Condiciones:
    vd              = 0 V
    vq              = 1 V
    T_load inicial  = 0 N*m
    T_load final    = 1 N*m
    t_load_step     = 25 ms
    dt              = 50 us
    T_END           = 50 ms

Este experimento NO modifica los módulos de producción.
No utiliza FOC, PI ni desacoplamiento.
"""

import csv
import math
from pathlib import Path

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.050

VD = 0.0
VQ = 1.0

T_LOAD_INITIAL = 0.0
T_LOAD_FINAL = 1.0
T_LOAD_STEP = 0.025

OUTPUT = Path("experiments/b0_7_plant_load_step.csv")


def inverse_park(vd: float, vq: float, theta_e: float):
    cos_t = math.cos(theta_e)
    sin_t = math.sin(theta_e)

    v_alpha = vd * cos_t - vq * sin_t
    v_beta = vd * sin_t + vq * cos_t

    return v_alpha, v_beta


def inverse_clarke(v_alpha: float, v_beta: float):
    va = v_alpha
    vb = -0.5 * v_alpha + (math.sqrt(3.0) / 2.0) * v_beta
    vc = -0.5 * v_alpha - (math.sqrt(3.0) / 2.0) * v_beta

    return va, vb, vc


def main():
    print("=" * 40)
    print(" B0.7 — PLANT LOAD STEP")
    print("=" * 40)

    plant = PMSMBase()

    n_steps = int(round(T_END / DT))
    rows = []

    states = plant.states

    rows.append([
        0.0,
        VD,
        VQ,
        T_LOAD_INITIAL,
        0.0,
        0.0,
        0.0,
        states["id"],
        states["iq"],
        0.0,
        states["omega_m"],
        states["theta_m"],
    ])

    for k in range(1, n_steps + 1):
        t = k * DT

        if t < T_LOAD_STEP:
            t_load = T_LOAD_INITIAL
        else:
            t_load = T_LOAD_FINAL

        theta_m = plant.states["theta_m"]
        theta_e = plant.params.n_pole_pairs * theta_m

        v_alpha, v_beta = inverse_park(VD, VQ, theta_e)
        va, vb, vc = inverse_clarke(v_alpha, v_beta)

        out = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=t_load,
            ),
            DT,
        )

        rows.append([
            t,
            VD,
            VQ,
            t_load,
            va,
            vb,
            vc,
            out.id,
            out.iq,
            out.te,
            out.omega_m,
            out.theta_m,
        ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "time_s",
            "vd_V",
            "vq_V",
            "t_load_Nm",
            "va_V",
            "vb_V",
            "vc_V",
            "id_A",
            "iq_A",
            "te_Nm",
            "omega_m_rad_s",
            "theta_m_rad",
        ])

        writer.writerows(rows)

    iq_values = [row[8] for row in rows]
    id_values = [row[7] for row in rows]
    te_values = [row[9] for row in rows]
    omega_values = [row[10] for row in rows]

    print(f"dt          = {DT:.9f} s")
    print(f"T_END       = {T_END:.6f} s")
    print(f"vd          = {VD:.6f} V")
    print(f"vq          = {VQ:.6f} V")
    print(f"T_load step = {T_LOAD_STEP:.6f} s")
    print(f"T_load init = {T_LOAD_INITIAL:.6f} N*m")
    print(f"T_load final= {T_LOAD_FINAL:.6f} N*m")
    print()
    print(f"iq final    = {iq_values[-1]:.9f} A")
    print(f"|iq| max    = {max(abs(x) for x in iq_values):.9f} A")
    print(f"|id| max    = {max(abs(x) for x in id_values):.9f} A")
    print(f"Te final    = {te_values[-1]:.9f} N*m")
    print(f"omega final = {omega_values[-1]:.9f} rad/s")
    print()
    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
