"""F1.3 — Comparación FOC + PI con y sin fricción no lineal.

Objetivo
--------
Comparar el comportamiento del mismo FOC + PI cuando la planta es:

    A) PMSMBase
    B) PMSMWithFriction

La única diferencia entre ambas ramas debe ser la presencia explícita
del término de fricción mecánica.

La arquitectura de control se conserva exactamente como en B2.2:

    referencia de velocidad
        -> SpeedController
        -> iq_ref
        -> FOC de corriente
        -> PMSM

Escenario
---------
    DT        = 50 us
    T_END     = 0.2 s
    omega_ref = 0 -> 100 rad/s en t = 0.05 s
    id_ref    = 0 A
    T_load    = 0 N*m

Fricción
--------
Los parámetros utilizados son los mismos del escenario F0/F1:

    Tc      = 0.5 N*m
    Ts      = 0.8 N*m
    omega_s = 10 rad/s
    delta   = 2
    B       = 0.01 N*m*s/rad

Estos valores son parámetros de escenario experimental.
No representan parámetros confirmados del Siemens 1FT7087.

Métricas
--------
Las métricas se calculan después de aplicar el escalón de velocidad:

    t >= 0.05 s

Se registran:

    MAE
    RMSE
    error máximo absoluto
    error final
    error medio en el último 10 % del ensayo
    sobreimpulso
    tiempo de establecimiento al 2 %

Además se conserva una trayectoria CSV conjunta para facilitar la
comparación posterior.
"""

from __future__ import annotations

import csv
import math
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
# CONFIGURACIÓN DEL ENSAYO
# ============================================================

DT = 50e-6
T_END = 0.200
STEPS = int(T_END / DT)

ID_REF = 0.0
T_LOAD = 0.0

OMEGA_LEVELS = [
    (0.000, 0.0),
    (0.050, 100.0),
]

REFERENCE_STEP_TIME = 0.050
OMEGA_REFERENCE_FINAL = 100.0


# ============================================================
# FRICCIÓN — ESCENARIO EXPERIMENTAL F0/F1
# ============================================================

FRICTION_PARAMETERS = StribeckFrictionParameters(
    tc=0.5,
    ts=0.8,
    omega_s=10.0,
    delta=2.0,
    b=0.01,
)


# ============================================================
# REFERENCIA DE VELOCIDAD
# ============================================================

def speed_reference(t: float) -> float:
    """Retorna la referencia de velocidad para el instante t."""
    omega_ref = 0.0

    for t0, value in OMEGA_LEVELS:
        if t >= t0:
            omega_ref = value

    return omega_ref


# ============================================================
# MÉTRICAS
# ============================================================

def calculate_metrics(
    history: list[dict[str, float]],
) -> dict[str, float]:
    """Calcula métricas de velocidad después del escalón."""

    analysis = [
        row
        for row in history
        if row["t"] >= REFERENCE_STEP_TIME
    ]

    if not analysis:
        raise RuntimeError("No hay muestras para calcular métricas.")

    errors = [
        abs(row["omega_ref"] - row["omega_m"])
        for row in analysis
    ]

    squared_errors = [
        (row["omega_ref"] - row["omega_m"]) ** 2
        for row in analysis
    ]

    signed_errors = [
        row["omega_ref"] - row["omega_m"]
        for row in analysis
    ]

    omega_values = [
        row["omega_m"]
        for row in analysis
    ]

    mae = sum(errors) / len(errors)

    rmse = math.sqrt(
        sum(squared_errors) / len(squared_errors)
    )

    max_abs_error = max(errors)

    final_error = (
        analysis[-1]["omega_ref"]
        - analysis[-1]["omega_m"]
    )

    final_abs_error = abs(final_error)

    # Último 10 % del intervalo analizado.
    n_tail = max(1, math.ceil(len(analysis) * 0.10))
    tail = analysis[-n_tail:]

    tail_errors = [
        row["omega_ref"] - row["omega_m"]
        for row in tail
    ]

    tail_abs_errors = [
        abs(error)
        for error in tail_errors
    ]

    mean_tail_error = sum(tail_errors) / len(tail_errors)
    mean_tail_abs_error = (
        sum(tail_abs_errors) / len(tail_abs_errors)
    )

    # Sobreimpulso respecto de la referencia final.
    overshoot_amount = max(
        0.0,
        max(omega_values) - OMEGA_REFERENCE_FINAL,
    )

    overshoot_percent = (
        100.0 * overshoot_amount / OMEGA_REFERENCE_FINAL
    )

    # Tiempo de establecimiento al 2 %.
    #
    # La banda es:
    #
    #   |e| <= 0.02 * 100 = 2 rad/s
    #
    # El instante reportado es el primero a partir del cual
    # todas las muestras posteriores permanecen dentro de la banda.
    settling_band = 0.02 * OMEGA_REFERENCE_FINAL

    settling_time = math.nan

    for index, row in enumerate(analysis):
        remaining_errors = [
            abs(
                future_row["omega_ref"]
                - future_row["omega_m"]
            )
            for future_row in analysis[index:]
        ]

        if all(error <= settling_band for error in remaining_errors):
            settling_time = row["t"]
            break

    return {
        "mae_rad_s": mae,
        "rmse_rad_s": rmse,
        "max_abs_error_rad_s": max_abs_error,
        "final_error_rad_s": final_error,
        "final_abs_error_rad_s": final_abs_error,
        "mean_tail_error_rad_s": mean_tail_error,
        "mean_tail_abs_error_rad_s": mean_tail_abs_error,
        "overshoot_percent": overshoot_percent,
        "settling_time_2pct_s": settling_time,
    }


# ============================================================
# EJECUCIÓN DE UNA RAMA
# ============================================================

def run_case(
    plant,
    friction_enabled: bool,
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Ejecuta una rama completa del experimento F1.3."""

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController()

    # Igual que B2.2: inicialización mediante un paso inicial
    # con tensión cero antes del ciclo principal.
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

        if friction_enabled:
            friction_torque = plant.friction_torque()
        else:
            friction_torque = 0.0

        history.append(
            {
                "t": t,
                "omega_ref": omega_ref,
                "omega_m": output.omega_m,
                "error_omega": omega_ref - output.omega_m,
                "iq_ref": iq_ref,
                "id": output.id,
                "iq": output.iq,
                "te": output.te,
                "friction_torque": friction_torque,
                "theta_m": output.theta_m,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    metrics = calculate_metrics(history)

    return history, metrics


# ============================================================
# CSV DE TRAYECTORIA
# ============================================================

def write_trajectory_csv(
    history_base: list[dict[str, float]],
    history_friction: list[dict[str, float]],
    output_file: str,
) -> None:
    """Escribe las dos trayectorias en un CSV conjunto."""

    if len(history_base) != len(history_friction):
        raise RuntimeError(
            "Las trayectorias tienen diferente número de muestras."
        )

    fieldnames = [
        "t",
        "omega_ref",
        "omega_base",
        "omega_friction",
        "error_base",
        "error_friction",
        "iq_ref_base",
        "iq_ref_friction",
        "id_base",
        "id_friction",
        "iq_base",
        "iq_friction",
        "te_base",
        "te_friction",
        "friction_torque",
        "theta_base",
        "theta_friction",
        "va_base",
        "vb_base",
        "vc_base",
        "va_friction",
        "vb_friction",
        "vc_friction",
    ]

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for base, friction in zip(
            history_base,
            history_friction,
        ):
            writer.writerow(
                {
                    "t": base["t"],
                    "omega_ref": base["omega_ref"],
                    "omega_base": base["omega_m"],
                    "omega_friction": friction["omega_m"],
                    "error_base": base["error_omega"],
                    "error_friction": friction["error_omega"],
                    "iq_ref_base": base["iq_ref"],
                    "iq_ref_friction": friction["iq_ref"],
                    "id_base": base["id"],
                    "id_friction": friction["id"],
                    "iq_base": base["iq"],
                    "iq_friction": friction["iq"],
                    "te_base": base["te"],
                    "te_friction": friction["te"],
                    "friction_torque": friction["friction_torque"],
                    "theta_base": base["theta_m"],
                    "theta_friction": friction["theta_m"],
                    "va_base": base["va"],
                    "vb_base": base["vb"],
                    "vc_base": base["vc"],
                    "va_friction": friction["va"],
                    "vb_friction": friction["vb"],
                    "vc_friction": friction["vc"],
                }
            )


# ============================================================
# CSV DE MÉTRICAS
# ============================================================

def write_metrics_csv(
    metrics_base: dict[str, float],
    metrics_friction: dict[str, float],
    output_file: str,
) -> None:
    """Escribe las métricas comparativas."""

    fieldnames = [
        "case",
        "mae_rad_s",
        "rmse_rad_s",
        "max_abs_error_rad_s",
        "final_error_rad_s",
        "final_abs_error_rad_s",
        "mean_tail_error_rad_s",
        "mean_tail_abs_error_rad_s",
        "overshoot_percent",
        "settling_time_2pct_s",
    ]

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerow(
            {
                "case": "PMSMBase",
                **metrics_base,
            }
        )

        writer.writerow(
            {
                "case": "PMSMWithFriction",
                **metrics_friction,
            }
        )


# ============================================================
# INFORME DE CONSOLA
# ============================================================

def print_metrics(
    case_name: str,
    metrics: dict[str, float],
) -> None:
    """Imprime las métricas de una rama."""

    print()
    print(case_name)
    print("----------------------------------------")
    print(
        f"MAE                 = "
        f"{metrics['mae_rad_s']:.9f} rad/s"
    )
    print(
        f"RMSE                = "
        f"{metrics['rmse_rad_s']:.9f} rad/s"
    )
    print(
        f"Max |error|         = "
        f"{metrics['max_abs_error_rad_s']:.9f} rad/s"
    )
    print(
        f"Error final         = "
        f"{metrics['final_error_rad_s']:.9f} rad/s"
    )
    print(
        f"|Error| final       = "
        f"{metrics['final_abs_error_rad_s']:.9f} rad/s"
    )
    print(
        f"Error medio final   = "
        f"{metrics['mean_tail_error_rad_s']:.9f} rad/s"
    )
    print(
        f"|Error| medio final = "
        f"{metrics['mean_tail_abs_error_rad_s']:.9f} rad/s"
    )
    print(
        f"Overshoot           = "
        f"{metrics['overshoot_percent']:.9f} %"
    )

    settling_time = metrics["settling_time_2pct_s"]

    if math.isnan(settling_time):
        print("Settling 2 %        = NO ALCANZADO")
    else:
        print(
            f"Settling 2 %        = "
            f"{settling_time:.9f} s"
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("========================================")
    print(" F1.3 — FOC + PI CON Y SIN FRICCIÓN")
    print("========================================")
    print(f"dt          = {DT:.8f} s")
    print(f"duration    = {T_END:.6f} s")
    print(f"steps       = {STEPS}")
    print(f"omega_ref   = {OMEGA_REFERENCE_FINAL:.6f} rad/s")
    print(f"omega step  = {REFERENCE_STEP_TIME:.6f} s")
    print(f"id_ref      = {ID_REF:.6f} A")
    print(f"T_load      = {T_LOAD:.6f} N*m")

    print()
    print("FRICTION SCENARIO")
    print("----------------------------------------")
    print(f"Tc          = {FRICTION_PARAMETERS.tc:.6f} N*m")
    print(f"Ts          = {FRICTION_PARAMETERS.ts:.6f} N*m")
    print(f"omega_s     = {FRICTION_PARAMETERS.omega_s:.6f} rad/s")
    print(f"delta       = {FRICTION_PARAMETERS.delta:.6f}")
    print(f"B           = {FRICTION_PARAMETERS.b:.6f} N*m*s/rad")

    # --------------------------------------------------------
    # Rama A — PMSMBase
    # --------------------------------------------------------

    base_plant = PMSMBase()

    history_base, metrics_base = run_case(
        plant=base_plant,
        friction_enabled=False,
    )

    # --------------------------------------------------------
    # Rama B — PMSMWithFriction
    # --------------------------------------------------------

    friction_model = StribeckFriction(
        FRICTION_PARAMETERS
    )

    friction_plant = PMSMWithFriction(
        friction=friction_model,
    )

    history_friction, metrics_friction = run_case(
        plant=friction_plant,
        friction_enabled=True,
    )

    # --------------------------------------------------------
    # Archivos de salida
    # --------------------------------------------------------

    trajectory_file = (
        "experiments/f1_3_foc_pi_friction_comparison.csv"
    )

    metrics_file = (
        "experiments/f1_3_foc_pi_friction_metrics.csv"
    )

    write_trajectory_csv(
        history_base=history_base,
        history_friction=history_friction,
        output_file=trajectory_file,
    )

    write_metrics_csv(
        metrics_base=metrics_base,
        metrics_friction=metrics_friction,
        output_file=metrics_file,
    )

    # --------------------------------------------------------
    # Resultados finales
    # --------------------------------------------------------

    print()
    print("========================================")
    print(" RESULTADOS F1.3")
    print("========================================")

    print_metrics(
        "A — PMSMBase",
        metrics_base,
    )

    print_metrics(
        "B — PMSMWithFriction",
        metrics_friction,
    )

    print()
    print("COMPARACIÓN FINAL")
    print("----------------------------------------")

    delta_mae = (
        metrics_friction["mae_rad_s"]
        - metrics_base["mae_rad_s"]
    )

    delta_rmse = (
        metrics_friction["rmse_rad_s"]
        - metrics_base["rmse_rad_s"]
    )

    delta_final = (
        metrics_friction["final_abs_error_rad_s"]
        - metrics_base["final_abs_error_rad_s"]
    )

    print(
        f"Δ MAE               = "
        f"{delta_mae:.9f} rad/s"
    )
    print(
        f"Δ RMSE              = "
        f"{delta_rmse:.9f} rad/s"
    )
    print(
        f"Δ |error| final     = "
        f"{delta_final:.9f} rad/s"
    )

    print()
    print(f"CSV trayectoria      = {trajectory_file}")
    print(f"CSV métricas         = {metrics_file}")


if __name__ == "__main__":
    main()
