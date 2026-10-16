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
# J1 — ANFIS INPUT SUFFICIENCY
# ============================================================
#
# Objetivo:
#   Generar trayectorias temporales instrumentadas para estudiar
#   si las entradas propuestas para ANFIS:
#
#       [e_omega, delta_e_omega, |iq|]
#
#   contienen información suficiente para la adaptación de Kp/Ki.
#
# IMPORTANTE:
#   - NO entrena ANFIS.
#   - NO genera etiquetas instantáneas.
#   - NO modifica B2.5.
#   - NO sobrescribe resultados existentes.
#   - int_w se registra como variable diagnóstica, no como entrada
#     ANFIS definitiva.
#
# Las configuraciones A/B/C proceden de las configuraciones
# candidatas ya documentadas en B2.5.
# ============================================================


DT = 50e-6
DURATION = 0.4
STEPS = int(round(DURATION / DT))

ID_REF = 0.0
T_LOAD = 0.0

KP_BASE = 5.2804
KI_BASE = 1.2693

# Tres configuraciones candidatas ya identificadas en B2.5.
CANDIDATE_CONFIGURATIONS = (
    ("A", 0.50, 0.50),
    ("B", 0.50, 2.00),
    ("C", 0.75, 2.00),
)

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

OUTPUT_DIR = Path("experiments/j1_anfis_analysis")
TRAJECTORY_FILE = OUTPUT_DIR / "j1_temporal_trajectories.csv"
SUMMARY_FILE = OUTPUT_DIR / "j1_run_summary.csv"


@dataclass(frozen=True)
class Scenario:
    name: str
    tc: float
    ts: float
    omega_s: float
    delta: float
    b: float


def speed_reference(t: float) -> float:
    """Mismo perfil temporal utilizado en B2.5."""

    if t < 0.05:
        return 0.0

    if t < 0.15:
        return +20.0

    if t < 0.25:
        return 0.0

    if t < 0.35:
        return -20.0

    return 0.0


def transition_for_time(t: float) -> str:
    """Asocia cada muestra con la transición temporal B2.5."""

    if 0.05 <= t < 0.15:
        return "0_to_plus20"

    if 0.15 <= t < 0.25:
        return "plus20_to_zero"

    if 0.25 <= t < 0.35:
        return "zero_to_minus20"

    if 0.35 <= t <= DURATION:
        return "minus20_to_zero"

    return "pre_profile"


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
    candidate_name: str,
    kp_factor: float,
    ki_factor: float,
) -> list[dict[str, float | str]]:
    """Ejecuta una trayectoria J1 instrumentada."""

    kp = KP_BASE * kp_factor
    ki = KI_BASE * ki_factor

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

    history: list[dict[str, float | str]] = []

    previous_error = 0.0

    for k in range(STEPS):
        t = (k + 1) * DT

        omega_ref = speed_reference(t)

        error = omega_ref - output.omega_m

        delta_error = error - previous_error

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
                "candidate": candidate_name,
                "scenario": scenario.name,
                "kp_factor": kp_factor,
                "ki_factor": ki_factor,
                "kp": kp,
                "ki": ki,
                "transition": transition_for_time(t),
                "omega_ref": omega_ref,
                "omega_m": output.omega_m,
                "error": error,
                "delta_error": delta_error,
                "int_w": speed_controller.int_w,
                "iq_ref": iq_ref,
                "abs_iq": abs(output.iq),
                "iq": output.iq,
                "id": output.id,
                "te": output.te,
                "tf": tf,
            }
        )

        previous_error = error

    return history


def validate_history(
    history: list[dict[str, float | str]],
) -> None:
    if not history:
        raise RuntimeError("La trayectoria J1 está vacía.")

    required = {
        "t",
        "candidate",
        "scenario",
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "transition",
        "omega_ref",
        "omega_m",
        "error",
        "delta_error",
        "int_w",
        "iq_ref",
        "abs_iq",
        "iq",
        "id",
        "te",
        "tf",
    }

    missing = required.difference(history[0].keys())

    if missing:
        raise RuntimeError(
            f"Faltan columnas en J1: {sorted(missing)}"
        )

    numeric_fields = {
        "t",
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "omega_ref",
        "omega_m",
        "error",
        "delta_error",
        "int_w",
        "iq_ref",
        "abs_iq",
        "iq",
        "id",
        "te",
        "tf",
    }

    for index, row in enumerate(history):
        for field in numeric_fields:
            value = float(row[field])

            if not math.isfinite(value):
                raise RuntimeError(
                    f"Valor no finito en fila {index}, campo {field}: {value}"
                )


def write_trajectories(
    rows: list[dict[str, float | str]],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "t",
        "candidate",
        "scenario",
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "transition",
        "omega_ref",
        "omega_m",
        "error",
        "delta_error",
        "int_w",
        "iq_ref",
        "abs_iq",
        "iq",
        "id",
        "te",
        "tf",
    ]

    with TRAJECTORY_FILE.open(
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


def summarize(
    history: list[dict[str, float | str]],
) -> dict[str, float | str]:
    errors = [abs(float(row["error"])) for row in history]
    iq_values = [float(row["abs_iq"]) for row in history]
    iq_ref_values = [abs(float(row["iq_ref"])) for row in history]
    integral_values = [float(row["int_w"]) for row in history]

    return {
        "candidate": history[0]["candidate"],
        "scenario": history[0]["scenario"],
        "kp": history[0]["kp"],
        "ki": history[0]["ki"],
        "samples": len(history),
        "mae_full": sum(errors) / len(errors),
        "max_abs_error": max(errors),
        "max_abs_iq": max(iq_values),
        "max_abs_iq_ref": max(iq_ref_values),
        "int_w_min": min(integral_values),
        "int_w_max": max(integral_values),
    }


def write_summary(
    rows: list[dict[str, float | str]],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with SUMMARY_FILE.open(
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
    """Una única corrida para verificar la instrumentación."""

    scenario = build_scenarios()[0]

    candidate_name, kp_factor, ki_factor = CANDIDATE_CONFIGURATIONS[0]

    print("=" * 60)
    print(" J1 — SMOKE TEST")
    print("=" * 60)
    print(f"candidate = {candidate_name}")
    print(f"scenario  = {scenario.name}")
    print(f"Kp        = {KP_BASE * kp_factor:.7f}")
    print(f"Ki        = {KI_BASE * ki_factor:.7f}")
    print(f"dt        = {DT:.7e}")
    print(f"duration  = {DURATION:.3f} s")
    print()

    history = run_experiment(
        scenario=scenario,
        candidate_name=candidate_name,
        kp_factor=kp_factor,
        ki_factor=ki_factor,
    )

    validate_history(history)

    summary = summarize(history)

    print("Resultado:")
    for key, value in summary.items():
        print(f"  {key:16s} = {value}")

    print()
    print(f"muestras = {len(history)}")
    print(f"primera  = {history[0]}")
    print(f"ultima   = {history[-1]}")
    print()
    print("J1 smoke test completado.")


def run_full_j1() -> None:
    """Ejecuta las 3 configuraciones x 4 escenarios."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, float | str]] = []
    summary_rows: list[dict[str, float | str]] = []

    scenarios = build_scenarios()

    total = len(CANDIDATE_CONFIGURATIONS) * len(scenarios)
    run_number = 0

    print("=" * 60)
    print(" J1 — ANFIS INPUT SUFFICIENCY")
    print("=" * 60)
    print(f"configuraciones = {len(CANDIDATE_CONFIGURATIONS)}")
    print(f"escenarios      = {len(scenarios)}")
    print(f"corridas        = {total}")
    print(f"dt              = {DT:.7e}")
    print(f"duration        = {DURATION:.3f} s")
    print()

    for scenario in scenarios:
        for candidate_name, kp_factor, ki_factor in CANDIDATE_CONFIGURATIONS:
            run_number += 1

            print(
                f"[{run_number:02d}/{total:02d}] "
                f"{scenario.name:16s} "
                f"{candidate_name} "
                f"Kp={KP_BASE * kp_factor:.6f} "
                f"Ki={KI_BASE * ki_factor:.6f}"
            )

            history = run_experiment(
                scenario=scenario,
                candidate_name=candidate_name,
                kp_factor=kp_factor,
                ki_factor=ki_factor,
            )

            validate_history(history)

            all_rows.extend(history)
            summary_rows.append(summarize(history))

    write_trajectories(all_rows)
    write_summary(summary_rows)

    print()
    print("=" * 60)
    print(" SALIDA J1")
    print("=" * 60)
    print(f"trayectorias = {TRAJECTORY_FILE}")
    print(f"resumen      = {SUMMARY_FILE}")
    print(f"muestras     = {len(all_rows)}")
    print(f"corridas     = {len(summary_rows)}")


def main() -> None:
    run_full_j1()


if __name__ == "__main__":
    main()
