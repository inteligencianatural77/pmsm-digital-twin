"""B2.3 — Lazo de velocidad cerrado con escalones de carga."""

from __future__ import annotations

import csv

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.200
STEPS = int(T_END / DT)

ID_REF = 0.0

OMEGA_REF = 100.0

LOAD_LEVELS = [
    (0.000, 0.0),
    (0.100, 5.0),
    (0.150, 10.0),
    (0.175, 5.0),
]


def load_reference(t: float) -> float:
    t_load = 0.0

    for t0, value in LOAD_LEVELS:
        if t >= t0:
            t_load = value

    return t_load


def main() -> None:
    plant = PMSMBase()

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController()

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=0.0,
            theta_m=plant.states["theta_m"],
        ),
        dt=DT,
    )

    history = []

    for k in range(STEPS):
        t = (k + 1) * DT

        t_load = load_reference(t)

        iq_ref = speed_controller.update(
            omega_ref=OMEGA_REF,
            omega_meas=output.omega_m,
            dt=DT,
        )

        va, vb, vc = foc.step(
            ia=output.ia,
            ib=output.ib,
            ic=output.ic,
            theta_m=output.theta_m,
            omega_m=output.omega_m,
            id_ref=ID_REF,
            iq_ref=iq_ref,
            dt=DT,
        )

        output = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=t_load,
                theta_m=output.theta_m,
            ),
            dt=DT,
        )

        history.append(
            {
                "t": t,
                "omega_ref": OMEGA_REF,
                "omega_m": output.omega_m,
                "iq_ref": iq_ref,
                "id": output.id,
                "iq": output.iq,
                "t_load": t_load,
                "te": output.te,
                "theta_m": output.theta_m,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    output_file = "experiments/b2_3_speed_load_steps.csv"

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=history[0].keys(),
        )
        writer.writeheader()
        writer.writerows(history)

    last = history[-1]

    print("B2.3 — Lazo de velocidad con escalones de carga")
    print(f"omega_ref final = {last['omega_ref']:.6f} rad/s")
    print(f"omega_m final   = {last['omega_m']:.6f} rad/s")
    print(f"iq_ref final    = {last['iq_ref']:.6f} A")
    print(f"iq final        = {last['iq']:.6f} A")
    print(f"id final        = {last['id']:.6f} A")
    print(f"T_load final    = {last['t_load']:.6f} N*m")
    print(f"Te final        = {last['te']:.6f} N*m")
    print(f"theta_m final   = {last['theta_m']:.6f} rad")
    print(f"CSV             = {output_file}")


if __name__ == "__main__":
    main()
