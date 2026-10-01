"""B1.5 — FOC + PMSMBase con cambios de referencia Iq.

Ensayo funcional de seguimiento de referencia de corriente q.

No modifica los módulos de producción.
Utiliza la arquitectura activa:
    FOC + PMSMBase
"""

from __future__ import annotations

import csv
from pathlib import Path

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.200

ID_REF = 0.0
T_LOAD = 0.0

IQ_LEVELS = (
    (0.000, 0.0),
    (0.050, 10.0),
    (0.100, 20.0),
    (0.150, 10.0),
)


def iq_reference(t: float) -> float:
    """Referencia Iq por tramos."""
    iq_ref = 0.0

    for start_time, value in IQ_LEVELS:
        if t >= start_time:
            iq_ref = value

    return iq_ref


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
            t_load=T_LOAD,
            theta_m=plant.states["theta_m"],
        ),
        dt=DT,
    )

    rows: list[dict[str, float]] = []

    n_steps = int(round(T_END / DT))

    for k in range(n_steps):
        t = (k + 1) * DT
        iq_ref = iq_reference(t)

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

        rows.append(
            {
                "t": t,
                "id_ref": ID_REF,
                "id": output.id,
                "iq_ref": iq_ref,
                "iq": output.iq,
                "omega_m": output.omega_m,
                "theta_m": output.theta_m,
                "te": output.te,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    output_csv = Path("experiments/b1_5_iq_reference_steps.csv")

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    last = rows[-1]

    print("========================================")
    print(" B1.5 — IQ REFERENCE STEPS")
    print("========================================")
    print(f"dt       = {DT:.9g} s")
    print(f"duration = {T_END:.6f} s")
    print(f"id_ref   = {ID_REF:.6f} A")
    print(f"t_load   = {T_LOAD:.6f} N*m")
    print()
    print("Iq reference:")
    for start_time, value in IQ_LEVELS:
        print(f"  t >= {start_time:.3f} s -> {value:.3f} A")
    print()
    print(f"final id = {last['id']:.6f} A")
    print(f"final iq = {last['iq']:.6f} A")
    print(f"final wm = {last['omega_m']:.6f} rad/s")
    print(f"final Te = {last['te']:.6f} N*m")
    print()
    print(f"samples  = {len(rows)}")
    print(f"output   = {output_csv}")


if __name__ == "__main__":
    main()
