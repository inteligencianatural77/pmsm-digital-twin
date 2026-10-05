"""B2.5C — Comparación de regulación después del arranque."""

from __future__ import annotations

import csv

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6

# 0.30 s de arranque + 0.50 s de regulación.
T_START = 0.300
T_REG = 0.500
T_END = T_START + T_REG

STEPS = int(T_END / DT)

ID_REF = 0.0
OMEGA_REF = 100.0

# Los escalones comienzan DESPUÉS del arranque.
LOAD_LEVELS = [
    (0.300, 0.0),
    (0.350, 5.0),
    (0.400, 10.0),
    (0.425, 5.0),
]

PI_CASES = [
    ("historico", 5.2804, 1.2693),
    ("wn2", 0.02586, 0.02586),
    ("wn4", 0.05172, 0.10344),
    ("wn6", 0.07758, 0.23274),
    ("wn8", 0.10344, 0.41376),
]


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
                "error": OMEGA_REF - output.omega_m,
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

    output_file = f"experiments/b2_5c_{name}.csv"

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=history[0].keys(),
        )
        writer.writeheader()
        writer.writerows(history)

    # Solo analizamos la fase de regulación.
    regulation = [
        row for row in history
        if row["t"] >= T_START
    ]

    steady_start = 0.750

    final_window = [
        row for row in history
        if row["t"] >= steady_start
    ]

    # Extremos posteriores a cada escalón.
    intervals = [
        ("5Nm", 0.350, 0.400),
        ("10Nm", 0.400, 0.425),
        ("5Nm_return", 0.425, 0.800),
    ]

    metrics = {
        "case": name,
        "kp_w": kp_w,
        "ki_w": ki_w,
        "omega_start_reg": regulation[0]["omega_m"],
        "error_start_reg": regulation[0]["error"],
        "omega_final": history[-1]["omega_m"],
        "error_final": history[-1]["error"],
        "max_abs_error_final_window": max(
            abs(row["error"]) for row in final_window
        ),
        "iq_ref_final": history[-1]["iq_ref"],
        "iq_final": history[-1]["iq"],
        "te_final": history[-1]["te"],
        "csv": output_file,
    }

    for label, t0, t1 in intervals:
        subset = [
            row for row in history
            if t0 <= row["t"] <= t1
        ]

        metrics[f"{label}_omega_min"] = min(
            row["omega_m"] for row in subset
        )
        metrics[f"{label}_omega_max"] = max(
            row["omega_m"] for row in subset
        )
        metrics[f"{label}_max_abs_error"] = max(
            abs(row["error"]) for row in subset
        )

    return metrics


def main() -> None:
    print("========== B2.5C — REGULACIÓN DESPUÉS DEL ARRANQUE ==========")
    print(f"Arranque       : 0.000 -> {T_START:.3f} s")
    print(f"Regulación     : {T_START:.3f} -> {T_END:.3f} s")
    print("Escalones      : 5 -> 10 -> 5 N*m")
    print()

    results = []

    for name, kp_w, ki_w in PI_CASES:
        result = run_case(name, kp_w, ki_w)
        results.append(result)

        print(
            f"{name:12s} | "
            f"omega_ini={result['omega_start_reg']:9.4f} | "
            f"omega_fin={result['omega_final']:9.4f} | "
            f"error_fin={result['error_final']:8.4f} | "
            f"iq_ref={result['iq_ref_final']:8.4f}"
        )

    summary_file = (
        "experiments/b2_5c_regulation_summary.csv"
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
