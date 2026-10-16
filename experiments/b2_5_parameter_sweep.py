from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.plant.pmsm_with_friction import PMSMWithFriction


# ============================================================
# B2.5 — PARAMETER SWEEP
# ============================================================

DT = 50e-6
DURATION = 0.4
STEPS = int(round(DURATION / DT))

ID_REF = 0.0
T_LOAD = 0.0

OMEGA_REF_LEVEL = 20.0

# Baseline histórico del controlador de velocidad.
KP_BASE = 5.2804
KI_BASE = 1.2693

# Primera exploración alrededor del baseline.
PARAMETER_FACTORS = (
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
)

# Escenarios exactamente compatibles con F1.5.
FRICTION_SCENARIOS = {
    "no_friction": {
        "tc": 0.0,
        "ts": 0.0,
        "omega_s": 10.0,
        "delta": 2.0,
        "b": 0.0,
    },
    "friction_base": {
        "tc": 0.5,
        "ts": 0.8,
        "omega_s": 10.0,
        "delta": 2.0,
        "b": 0.01,
    },
    "friction_medium": {
        "tc": 0.75,
        "ts": 1.20,
        "omega_s": 10.0,
        "delta": 2.0,
        "b": 0.015,
    },
    "friction_high": {
        "tc": 1.0,
        "ts": 1.60,
        "omega_s": 10.0,
        "delta": 2.0,
        "b": 0.020,
    },
}

TRANSITIONS = (
    ("0_to_plus20", 0.05, 0.15, +20.0),
    ("plus20_to_zero", 0.15, 0.25, 0.0),
    ("zero_to_minus20", 0.25, 0.35, -20.0),
    ("minus20_to_zero", 0.35, 0.40, 0.0),
)

METRICS_FILE = Path(
    "experiments/b2_5_parameter_sweep_metrics.csv"
)

CONFIG_FILE = Path(
    "experiments/b2_5_parameter_sweep_config.csv"
)


@dataclass(frozen=True)
class Scenario:
    name: str
    tc: float
    ts: float
    omega_s: float
    delta: float
    b: float


def speed_reference(t: float) -> float:
    """Mismo perfil de referencia utilizado en F1.4/F1.5."""

    if t < 0.05:
        return 0.0

    if t < 0.15:
        return +20.0

    if t < 0.25:
        return 0.0

    if t < 0.35:
        return -20.0

    return 0.0


def build_scenarios() -> list[Scenario]:
    return [
        Scenario(name=name, **values)
        for name, values in FRICTION_SCENARIOS.items()
    ]


def build_plant(scenario: Scenario):
    if scenario.name == "no_friction":
        return PMSMBase()

    friction = StribeckFriction(
        StribeckFrictionParameters(
            tc=scenario.tc,
            ts=scenario.ts,
            omega_s=scenario.omega_s,
            delta=scenario.delta,
            b=scenario.b,
        )
    )

    return PMSMWithFriction(friction=friction)


def run_experiment(
    scenario: Scenario,
    kp: float,
    ki: float,
) -> list[dict[str, float]]:
    """Ejecuta una combinación Kp/Ki y conserva la trayectoria."""

    plant = build_plant(scenario)

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController(
        kp_w=kp,
        ki_w=ki,
    )

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=T_LOAD,
        ),
        dt=DT,
    )

    history: list[dict[str, float]] = []

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
            ),
            dt=DT,
        )

        tf = 0.0
        if hasattr(plant, "friction_torque"):
            tf = plant.friction_torque()

        history.append(
            {
                "t": t,
                "omega_ref": omega_ref,
                "omega_m": output.omega_m,
                "error": omega_ref - output.omega_m,
                "iq_ref": iq_ref,
                "iq": output.iq,
                "id": output.id,
                "te": output.te,
                "tf": tf,
            }
        )

    return history


def select_transition(
    history: list[dict[str, float]],
    start: float,
    end: float,
) -> list[dict[str, float]]:
    """
    Selección temporal reproducible.

    Se utiliza [start, end) para evitar incluir en una transición
    la primera muestra de la siguiente referencia.
    """

    if math.isclose(end, DURATION):
        return [
            row
            for row in history
            if start <= row["t"] <= end
        ]

    return [
        row
        for row in history
        if start <= row["t"] < end
    ]


def calculate_mae(rows: list[dict[str, float]]) -> float:
    return sum(abs(row["error"]) for row in rows) / len(rows)


def calculate_rmse(rows: list[dict[str, float]]) -> float:
    return math.sqrt(
        sum(row["error"] ** 2 for row in rows) / len(rows)
    )


def calculate_settling_time(
    rows: list[dict[str, float]],
    target: float,
    start: float,
) -> float:
    """
    Tiempo de establecimiento al 2 % para referencias no nulas.

    Para referencia cero se devuelve NaN porque un criterio relativo
    de 2 % no está definido.
    """

    if target == 0.0:
        return math.nan

    tolerance = 0.02 * abs(target)

    for index, row in enumerate(rows):
        if abs(row["error"]) > tolerance:
            continue

        remaining = rows[index:]

        if all(abs(item["error"]) <= tolerance for item in remaining):
            return row["t"] - start

    return math.nan


def calculate_overshoot(
    rows: list[dict[str, float]],
    target: float,
) -> float:
    """
    Sobreimpulso respecto de la magnitud de referencia.

    Para referencia cero no se define.
    """

    if target == 0.0:
        return math.nan

    magnitude = abs(target)

    if target > 0:
        peak = max(row["omega_m"] for row in rows)
        overshoot = max(0.0, peak - target)
    else:
        peak = min(row["omega_m"] for row in rows)
        overshoot = max(0.0, abs(peak) - magnitude)

    return 100.0 * overshoot / magnitude


def calculate_transition_metrics(
    history: list[dict[str, float]],
    transition_name: str,
    start: float,
    end: float,
    target: float,
    scenario: Scenario,
    kp_factor: float,
    ki_factor: float,
    kp: float,
    ki: float,
) -> dict[str, float | str]:

    rows = select_transition(history, start, end)

    if not rows:
        raise RuntimeError(
            f"No hay muestras para la transición {transition_name}."
        )

    return {
        "scenario": scenario.name,
        "transition": transition_name,
        "start_s": start,
        "end_s": end,
        "reference_rad_s": target,

        "kp_factor": kp_factor,
        "ki_factor": ki_factor,
        "kp": kp,
        "ki": ki,

        "mae_rad_s": calculate_mae(rows),
        "rmse_rad_s": calculate_rmse(rows),

        "final_abs_error_rad_s": abs(rows[-1]["error"]),
        "max_abs_error_rad_s": max(
            abs(row["error"]) for row in rows
        ),

        "settling_time_s": calculate_settling_time(
            rows,
            target,
            start,
        ),

        "overshoot_percent": calculate_overshoot(
            rows,
            target,
        ),

        "iq_ref_max_A": max(
            abs(row["iq_ref"]) for row in rows
        ),

        "te_max_Nm": max(
            abs(row["te"]) for row in rows
        ),

        "tf_max_Nm": max(
            abs(row["tf"]) for row in rows
        ),
    }


def write_metrics(rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with METRICS_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def write_config() -> None:
    rows = []

    for scenario in build_scenarios():
        for kp_factor in PARAMETER_FACTORS:
            for ki_factor in PARAMETER_FACTORS:
                rows.append(
                    {
                        "scenario": scenario.name,
                        "tc": scenario.tc,
                        "ts": scenario.ts,
                        "omega_s": scenario.omega_s,
                        "delta": scenario.delta,
                        "b": scenario.b,
                        "kp_base": KP_BASE,
                        "ki_base": KI_BASE,
                        "kp_factor": kp_factor,
                        "ki_factor": ki_factor,
                        "kp": KP_BASE * kp_factor,
                        "ki": KI_BASE * ki_factor,
                        "dt_s": DT,
                        "duration_s": DURATION,
                        "id_ref_A": ID_REF,
                        "t_load_Nm": T_LOAD,
                    }
                )

    fieldnames = list(rows[0].keys())

    with CONFIG_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def run_smoke_test() -> None:
    """
    Ejecuta solamente el baseline:
    escenario sin fricción, factor Kp=1, factor Ki=1.

    Debe utilizarse antes del sweep completo.
    """

    scenario = Scenario(
        name="no_friction",
        **FRICTION_SCENARIOS["no_friction"],
    )

    kp_factor = 1.0
    ki_factor = 1.0

    kp = KP_BASE * kp_factor
    ki = KI_BASE * ki_factor

    print("=" * 40)
    print(" B2.5 — SMOKE TEST")
    print("=" * 40)
    print(f"Kp = {kp:.7f}")
    print(f"Ki = {ki:.7f}")
    print("scenario = no_friction")
    print()

    history = run_experiment(
        scenario=scenario,
        kp=kp,
        ki=ki,
    )

    rows = []

    for transition_name, start, end, target in TRANSITIONS:
        metrics = calculate_transition_metrics(
            history=history,
            transition_name=transition_name,
            start=start,
            end=end,
            target=target,
            scenario=scenario,
            kp_factor=kp_factor,
            ki_factor=ki_factor,
            kp=kp,
            ki=ki,
        )

        rows.append(metrics)

        print(f"[{transition_name}]")
        print(f"  MAE       = {metrics['mae_rad_s']:.9f}")
        print(f"  RMSE      = {metrics['rmse_rad_s']:.9f}")
        print(
            "  final |e| = "
            f"{metrics['final_abs_error_rad_s']:.9f}"
        )
        print()

    print("Smoke test completado.")
    print()


def run_full_sweep() -> None:
    scenarios = build_scenarios()

    total_runs = (
        len(scenarios)
        * len(PARAMETER_FACTORS)
        * len(PARAMETER_FACTORS)
    )

    print("=" * 40)
    print(" B2.5 — PARAMETER SWEEP")
    print("=" * 40)
    print(f"Escenarios = {len(scenarios)}")
    print(f"Factores   = {len(PARAMETER_FACTORS)} x "
          f"{len(PARAMETER_FACTORS)}")
    print(f"Corridas   = {total_runs}")
    print()

    all_metrics = []
    run_number = 0

    for scenario in scenarios:
        print("-" * 40)
        print(f"ESCENARIO: {scenario.name}")
        print("-" * 40)

        for kp_factor in PARAMETER_FACTORS:
            for ki_factor in PARAMETER_FACTORS:
                run_number += 1

                kp = KP_BASE * kp_factor
                ki = KI_BASE * ki_factor

                print(
                    f"[{run_number:03d}/{total_runs:03d}] "
                    f"Kp={kp:.6f} "
                    f"Ki={ki:.6f}"
                )

                history = run_experiment(
                    scenario=scenario,
                    kp=kp,
                    ki=ki,
                )

                for transition_name, start, end, target in TRANSITIONS:
                    metrics = calculate_transition_metrics(
                        history=history,
                        transition_name=transition_name,
                        start=start,
                        end=end,
                        target=target,
                        scenario=scenario,
                        kp_factor=kp_factor,
                        ki_factor=ki_factor,
                        kp=kp,
                        ki=ki,
                    )

                    all_metrics.append(metrics)

    write_metrics(all_metrics)
    write_config()

    print()
    print("=" * 40)
    print(" SALIDA")
    print("=" * 40)
    print(f"Métricas = {METRICS_FILE}")
    print(f"Config   = {CONFIG_FILE}")
    print(
        f"Filas métricas = {len(all_metrics)}"
    )


def main() -> None:
    run_full_sweep()


if __name__ == "__main__":
    main()
