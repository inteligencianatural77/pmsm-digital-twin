"""B2.2 — Integración del PI de velocidad con el FOC de corriente."""

from __future__ import annotations

import csv

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.200
STEPS = int(T_END / DT)

ID_REF = 0.0
T_LOAD = 0.0

OMEGA_LEVELS = [
    (0.000, 0.0),
    (0.050, 100.0),
]


def speed_reference(t: float) -> float:
    omega_ref = 0.0

    for t0, value in OMEGA_LEVELS:
        if t >= t0:
            omega_ref = value

    return omega_ref


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
            t_load=T_LOAD,
            theta_m=plant.states["theta_m"],
        ),
        dt=DT,
    )

    history = []

    for k in range(STEPS):
        t = (k + 1) * DT

        omega_ref = speed_reference(t)

        iq_ref = speed_controller.update(
            omega_ref=omega_ref,
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
                t_load=T_LOAD,
                theta_m=output.theta_m,
            ),
            dt=DT,
        )

        history.append(
            {
                "t": t,
                "omega_ref": omega_ref,
                "omega_m": output.omega_m,
                "iq_ref": iq_ref,
                "id": output.id,
                "iq": output.iq,
                "te": output.te,
                "theta_m": output.theta_m,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    output_file = "experiments/b2_2_speed_closed_loop.csv"

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=history[0].keys(),
        )
        writer.writeheader()
        writer.writerows(history)

    last = history[-1]

    print("B2.2 — PI de velocidad + FOC de corriente")
    print(f"omega_ref final = {last['omega_ref']:.6f} rad/s")
    print(f"omega_m final   = {last['omega_m']:.6f} rad/s")
    print(f"iq_ref final    = {last['iq_ref']:.6f} A")
    print(f"iq final        = {last['iq']:.6f} A")
    print(f"id final        = {last['id']:.6f} A")
    print(f"Te final        = {last['te']:.6f} N*m")
    print(f"theta_m final   = {last['theta_m']:.6f} rad")
    print(f"CSV             = {output_file}")


if __name__ == "__main__":
    main()
