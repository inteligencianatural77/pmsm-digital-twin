"""B2.5A — Barrido de sintonía del PI de velocidad."""

from __future__ import annotations

import csv

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 1.000
STEPS = int(T_END / DT)

ID_REF = 0.0
OMEGA_REF = 100.0

LOAD_LEVELS = [
    (0.000, 0.0),
    (0.100, 5.0),
    (0.150, 10.0),
    (0.175, 5.0),
]

# Parámetros M4.
KT = 1.5 * 4 * 0.107245
J = 0.00416

# Referencia histórica + candidatas críticamente amortiguadas.
PI_CASES = [
    ("historico", 5.2804, 1.2693),
]

for wn in (2.0, 4.0, 6.0, 8.0):
    kp = 2.0 * J * wn / KT
    ki = J * wn * wn / KT
    PI_CASES.append((f"wn{wn:g}", kp, ki))


def load_reference(t: float) -> float:
    t_load = 0.0

    for t0, value in LOAD_LEVELS:
        if t >= t0:
            t_load = value

    return t_load


def run_case(name: str, kp_w: float, ki_w: float) -> dict:
    plant = PMSMBase()

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController(
        kp_w=kp_w,
        ki_w=ki_w,
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
            ),
            dt=DT,
        )

        error = OMEGA_REF - output.omega_m

        history.append(
            {
                "t": t,
                "omega_ref": OMEGA_REF,
                "omega_m": output.omega_m,
                "error": error,
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

    output_file = (
        f"experiments/b2_5a_{name}.csv"
    )

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=history[0].keys(),
        )
        writer.writeheader()
        writer.writerows(history)

    last = history[-1]

    window = [
        row for row in history
        if row["t"] >= 0.900
    ]

    max_abs_error = max(
        abs(row["error"])
        for row in window
    )

    result = {
        "case": name,
        "kp_w": kp_w,
        "ki_w": ki_w,
        "omega_final": last["omega_m"],
        "error_final": last["error"],
        "iq_ref_final": last["iq_ref"],
        "iq_final": last["iq"],
        "te_final": last["te"],
        "max_abs_error_0p9_1p0": max_abs_error,
        "csv": output_file,
    }

    return result


def main() -> None:
    print("========== B2.5A — BARRIDO DE SINTONÍA PI ==========")
    print(f"DT    = {DT:.8f} s")
    print(f"T_END = {T_END:.3f} s")
    print()

    results = []

    for name, kp_w, ki_w in PI_CASES:
        result = run_case(name, kp_w, ki_w)
        results.append(result)

        print(
            f"{name:12s} | "
            f"Kp={kp_w:8.5f} | "
            f"Ki={ki_w:8.5f} | "
            f"omega_final={result['omega_final']:10.6f} | "
            f"error_final={result['error_final']:9.6f} | "
            f"iq_ref={result['iq_ref_final']:9.6f}"
        )

    summary_file = (
        "experiments/b2_5a_pi_sweep_summary.csv"
    )

    with open(summary_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Resumen CSV = {summary_file}")


if __name__ == "__main__":
    main()
