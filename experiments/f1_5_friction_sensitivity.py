"""F1.5 — Sensibilidad del FOC + PI frente a la magnitud de la fricción.

Objetivo
--------
Evaluar cómo cambia la respuesta del mismo FOC + PI cuando aumenta
sistemáticamente la magnitud de la fricción no lineal.

La arquitectura de control permanece constante:

    referencia de velocidad
        -> SpeedController
        -> iq_ref
        -> FOC
        -> PMSM

La única variable experimental es la magnitud de la fricción.

Los parámetros de fricción son escenarios experimentales.
No representan parámetros confirmados del Siemens 1FT7087.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.plant.pmsm_with_friction import PMSMWithFriction


# ============================================================
# CONFIGURACIÓN
# ============================================================

DT = 50e-6
T_END = 0.400
STEPS = int(T_END / DT)

ID_REF = 0.0
T_LOAD = 0.0

OMEGA_LEVELS = [
    (0.000, 0.0),
    (0.050, 20.0),
    (0.150, 0.0),
    (0.250, -20.0),
    (0.350, 0.0),
]

TRANSITIONS = [
    ("0_to_plus20", 0.050, 0.150),
    ("plus20_to_zero", 0.150, 0.250),
    ("zero_to_minus20", 0.250, 0.350),
    ("minus20_to_zero", 0.350, 0.400),
]

OMEGA_S = 10.0
DELTA = 2.0


# ============================================================
# ESCENARIOS
# ============================================================

@dataclass(frozen=True)
class FrictionScenario:
    name: str
    tc: float
    ts: float
    b: float


SCENARIOS = [
    FrictionScenario(
        name="no_friction",
        tc=0.0,
        ts=0.0,
        b=0.0,
    ),
    FrictionScenario(
        name="friction_base",
        tc=0.5,
        ts=0.8,
        b=0.01,
    ),
    FrictionScenario(
        name="friction_medium",
        tc=0.75,
        ts=1.20,
        b=0.015,
    ),
    FrictionScenario(
        name="friction_high",
        tc=1.0,
        ts=1.60,
        b=0.020,
    ),
]


# ============================================================
# REFERENCIA
# ============================================================

def speed_reference(t: float) -> float:
    omega_ref = OMEGA_LEVELS[0][1]

    for t0, value in OMEGA_LEVELS:
        if t >= t0:
            omega_ref = value

    return omega_ref


# ============================================================
# FRICCIÓN
# ============================================================

def build_friction(
    scenario: FrictionScenario,
) -> StribeckFriction | None:

    if scenario.name == "no_friction":
        return None

    return StribeckFriction(
        StribeckFrictionParameters(
            tc=scenario.tc,
            ts=scenario.ts,
            omega_s=OMEGA_S,
            delta=DELTA,
            b=scenario.b,
        )
    )


# ============================================================
# PLANTA
# ============================================================

def build_plant(
    friction: StribeckFriction | None,
):
    if friction is None:
        return PMSMBase()

    return PMSMWithFriction(
        friction=friction,
    )


# ============================================================
# SIMULACIÓN
# ============================================================

def run_scenario(
    scenario: FrictionScenario,
) -> list[dict[str, float]]:

    plant = build_plant(
        build_friction(scenario)
    )

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController()

    # Inicialización idéntica a B2.2.
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

        if isinstance(plant, PMSMWithFriction):
            tf = plant.friction_torque()
        else:
            tf = 0.0

        error = omega_ref - output.omega_m

        history.append(
            {
                "scenario": scenario.name,
                "t": t,
                "omega_ref": omega_ref,
                "omega_m": output.omega_m,
                "error": error,
                "id": output.id,
                "iq": output.iq,
                "iq_ref": iq_ref,
                "te": output.te,
                "tf": tf,
            }
        )

    return history


# ============================================================
# MÉTRICAS
# ============================================================

def calculate_transition_metrics(
    history: list[dict[str, float]],
    start: float,
    end: float,
) -> dict[str, float]:

    # El extremo derecho pertenece a la siguiente transición,
    # porque la referencia cambia exactamente en ese instante.
    # Para el último intervalo se permite incluir la muestra final.
    if end >= T_END:
        analysis = [
            row
            for row in history
            if start <= row["t"] <= end
        ]
    else:
        analysis = [
            row
            for row in history
            if start <= row["t"] < end
        ]

    if not analysis:
        raise RuntimeError(
            f"No hay muestras para {start} -> {end}."
        )

    errors = [
        row["error"]
        for row in analysis
    ]

    abs_errors = [
        abs(error)
        for error in errors
    ]

    mae = sum(abs_errors) / len(abs_errors)

    rmse = math.sqrt(
        sum(error ** 2 for error in errors)
        / len(errors)
    )

    final_abs_error = abs(
        analysis[-1]["error"]
    )

    max_abs_error = max(abs_errors)

    iq_ref_max = max(
        abs(row["iq_ref"])
        for row in analysis
    )

    te_max = max(
        abs(row["te"])
        for row in analysis
    )

    tf_max = max(
        abs(row["tf"])
        for row in analysis
    )

    return {
        "start": start,
        "end": end,
        "reference": analysis[0]["omega_ref"],
        "mae": mae,
        "rmse": rmse,
        "final_abs_error": final_abs_error,
        "max_abs_error": max_abs_error,
        "iq_ref_max": iq_ref_max,
        "te_max": te_max,
        "tf_max": tf_max,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    trajectory_file = (
        "experiments/f1_5_friction_sensitivity.csv"
    )

    metrics_file = (
        "experiments/f1_5_friction_sensitivity_metrics.csv"
    )

    all_history = []
    all_metrics = []

    print("=" * 40)
    print(" F1.5 — SENSIBILIDAD A LA FRICCIÓN")
    print("=" * 40)
    print(f"dt          = {DT:.8f} s")
    print(f"duration    = {T_END:.6f} s")
    print(f"steps       = {STEPS}")
    print(f"id_ref      = {ID_REF:.6f} A")
    print(f"T_load      = {T_LOAD:.6f} N*m")
    print()

    print("SCENARIOS")
    print("-" * 40)

    for scenario in SCENARIOS:
        print(
            f"{scenario.name:18s} : "
            f"Tc={scenario.tc:.3f}, "
            f"Ts={scenario.ts:.3f}, "
            f"B={scenario.b:.3f}"
        )

    print()

    for scenario in SCENARIOS:

        print("=" * 40)
        print(f" ESCENARIO: {scenario.name}")
        print("=" * 40)

        history = run_scenario(scenario)

        all_history.extend(history)

        for (
            transition_name,
            start,
            end,
        ) in TRANSITIONS:

            metrics = calculate_transition_metrics(
                history,
                start,
                end,
            )

            metrics["scenario"] = scenario.name
            metrics["transition"] = transition_name

            all_metrics.append(metrics)

            print()
            print(
                f"[{transition_name}] "
                f"{start:.3f} -> {end:.3f} s"
            )

            print(
                f"Referencia          = "
                f"{metrics['reference']:.6f} rad/s"
            )

            print(
                f"MAE                 = "
                f"{metrics['mae']:.9f}"
            )

            print(
                f"RMSE                = "
                f"{metrics['rmse']:.9f}"
            )

            print(
                f"Error final abs.    = "
                f"{metrics['final_abs_error']:.9f}"
            )

            print(
                f"Max error abs.      = "
                f"{metrics['max_abs_error']:.9f}"
            )

            print(
                f"|iq_ref| máximo     = "
                f"{metrics['iq_ref_max']:.9f} A"
            )

            print(
                f"|Te| máximo         = "
                f"{metrics['te_max']:.9f} N*m"
            )

            print(
                f"|Tf| máximo         = "
                f"{metrics['tf_max']:.9f} N*m"
            )

    # ========================================================
    # TRAYECTORIA
    # ========================================================

    trajectory_fields = [
        "scenario",
        "t",
        "omega_ref",
        "omega_m",
        "error",
        "id",
        "iq",
        "iq_ref",
        "te",
        "tf",
    ]

    with open(
        trajectory_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=trajectory_fields,
        )

        writer.writeheader()
        writer.writerows(all_history)

    # ========================================================
    # MÉTRICAS
    # ========================================================

    metric_fields = [
        "scenario",
        "transition",
        "start",
        "end",
        "reference",
        "mae",
        "rmse",
        "final_abs_error",
        "max_abs_error",
        "iq_ref_max",
        "te_max",
        "tf_max",
    ]

    with open(
        metrics_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=metric_fields,
        )

        writer.writeheader()
        writer.writerows(all_metrics)

    print()
    print("=" * 40)
    print(" SALIDA")
    print("=" * 40)
    print(f"CSV trayectoria = {trajectory_file}")
    print(f"CSV métricas    = {metrics_file}")


if __name__ == "__main__":
    main()
