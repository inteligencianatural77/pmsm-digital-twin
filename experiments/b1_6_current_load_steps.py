"""B1.6 — FOC + PMSMBase con escalones de carga.

Ensayo funcional de corriente cerrada bajo cambios de torque de carga.

No modifica los módulos de producción.
"""

from __future__ import annotations

import csv
from pathlib import Path

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.200

ID_REF = 0.0
IQ_REF = 10.0

LOAD_LEVELS = (
    (0.000, 0.0),
    (0.050, 5.0),
    (0.100, 10.0),
    (0.150, 5.0),
)


def load_reference(t: float) -> float:
    """Torque de carga por tramos."""
    t_load = 0.0

    for start_time, value in LOAD_LEVELS:
        if t >= start_time:
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

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=0.0,
        ),
        dt=DT,
    )

    rows: list[dict[str, float]] = []

    n_steps = int(round(T_END / DT))

    for k in range(n_steps):
        t = (k + 1) * DT
        t_load = load_reference(t)

        va, vb, vc = foc.step(
            ia=output.ia,
            ib=output.ib,
            ic=output.ic,
            theta_m=output.theta_m,
            omega_m=output.omega_m,
            id_ref=ID_REF,
            iq_ref=IQ_REF,
            dt=DT,
        )

        output = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=t_load,
            ),
            dt=DT,
        )

        rows.append(
            {
                "t": t,
                "id_ref": ID_REF,
                "id": output.id,
                "iq_ref": IQ_REF,
                "iq": output.iq,
                "t_load": t_load,
                "te": output.te,
                "omega_m": output.omega_m,
                "theta_m": output.theta_m,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    output_csv = Path("experiments/b1_6_current_load_steps.csv")

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    last = rows[-1]

    print("========================================")
    print(" B1.6 — CURRENT + LOAD STEPS")
    print("========================================")
    print(f"dt       = {DT:.9g} s")
    print(f"duration = {T_END:.6f} s")
    print(f"id_ref   = {ID_REF:.6f} A")
    print(f"iq_ref   = {IQ_REF:.6f} A")
    print()
    print("T_load:")
    for start_time, value in LOAD_LEVELS:
        print(f"  t >= {start_time:.3f} s -> {value:.3f} N*m")
    print()
    print(f"final id = {last['id']:.6f} A")
    print(f"final iq = {last['iq']:.6f} A")
    print(f"final Te = {last['te']:.6f} N*m")
    print(f"final wm = {last['omega_m']:.6f} rad/s")
    print()
    print(f"samples  = {len(rows)}")
    print(f"output   = {output_csv}")


if __name__ == "__main__":
    main()
