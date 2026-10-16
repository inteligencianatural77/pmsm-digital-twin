"""F1.4 — Baja velocidad y reversión con FOC + PI.

Objetivo
--------
Evaluar el efecto del modelo experimental de fricción no lineal
durante operación a baja velocidad, paso por cero y reversión.

Se comparan dos plantas bajo exactamente la misma arquitectura
de control:

    A) PMSMBase
    B) PMSMWithFriction

La única diferencia entre ambas ramas es la presencia del término
de fricción mecánica.

Arquitectura:

    omega_ref
        -> SpeedController
        -> iq_ref
        -> FOC
        -> PMSM

Escenario de referencia:

    0 rad/s       t = 0.00 s
    +20 rad/s     t = 0.05 s
      0 rad/s     t = 0.15 s
    -20 rad/s     t = 0.25 s
      0 rad/s     t = 0.35 s

Duración total:

    0.40 s

Paso:

    50 us

La fricción utiliza los mismos parámetros experimentales
empleados en F0, F1.2 y F1.3.

Estos parámetros NO son parámetros confirmados del
Siemens 1FT7087.
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
from pmsm_hybrid_control.plant.pmsm_with_friction import (
    PMSMWithFriction,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

DT = 50e-6
T_END = 0.400
STEPS = int(round(T_END / DT))

ID_REF = 0.0
T_LOAD = 0.0

REFERENCE_LEVELS = [
    (0.000, 0.0),
    (0.050, 20.0),
    (0.150, 0.0),
    (0.250, -20.0),
    (0.350, 0.0),
]


# ============================================================
# FRICCIÓN — MISMO ESCENARIO F0/F1.3
# ============================================================

FRICTION_PARAMETERS = StribeckFrictionParameters(
    tc=0.5,
    ts=0.8,
    omega_s=10.0,
    delta=2.0,
    b=0.01,
)


# ============================================================
# TRANSICIONES A ANALIZAR
# ============================================================

SEGMENTS = [
    {
        "name": "0_to_plus20",
        "start": 0.050,
        "end": 0.150,
        "reference": 20.0,
    },
    {
        "name": "plus20_to_zero",
        "start": 0.150,
        "end": 0.250,
        "reference": 0.0,
    },
    {
        "name": "zero_to_minus20",
        "start": 0.250,
        "end": 0.350,
        "reference": -20.0,
    },
    {
        "name": "minus20_to_zero",
        "start": 0.350,
        "end": 0.400,
        "reference": 0.0,
    },
]


# ============================================================
# REFERENCIA
# ============================================================

def speed_reference(t: float) -> float:
    """Retorna la referencia de velocidad para t."""

    omega_ref = REFERENCE_LEVELS[0][1]

    for t0, value in REFERENCE_LEVELS:
        if t >= t0:
            omega_ref = value
        else:
            break

    return omega_ref


# ============================================================
# EJECUCIÓN DE UNA PLANTA
# ============================================================

def run_case(
    plant,
    friction_enabled: bool,
) -> list[dict[str, float]]:
    """Ejecuta el FOC + PI sobre una planta."""

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController()

    # Igual que B2.2/F1.3.
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
                "error_omega": (
                    omega_ref - output.omega_m
                ),
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

    return history


# ============================================================
# MÉTRICAS POR SEGMENTO
# ============================================================

def segment_metrics(
    history: list[dict[str, float]],
    start: float,
    end: float,
    reference: float,
) -> dict[str, float]:
    """Calcula métricas para una transición."""

    rows = [
        row
        for row in history
        if row["t"] >= start
        and row["t"] < end
    ]

    if not rows:
        raise RuntimeError(
            f"No hay muestras en segmento {start} - {end}."
        )

    errors = [
        row["error_omega"]
        for row in rows
    ]

    abs_errors = [
        abs(error)
        for error in errors
    ]

    mae = sum(abs_errors) / len(abs_errors)

    rmse = math.sqrt(
        sum(error * error for error in errors)
        / len(errors)
    )

    max_abs_error = max(abs_errors)

    final_error = errors[-1]
    final_abs_error = abs(final_error)

    # ========================================================
    # Sobreimpulso / subimpulso
    #
    # Para referencias positivas:
    #     overshoot = max(omega - ref, 0)
    #
    # Para referencias negativas:
    #     overshoot = max(ref - omega, 0)
    #
    # Para referencia cero no se calcula como porcentaje.
    # ========================================================

    if reference > 0.0:
        overshoot_amount = max(
            0.0,
            max(row["omega_m"] for row in rows)
            - reference,
        )

        overshoot_percent = (
            100.0 * overshoot_amount / abs(reference)
        )

        undershoot_amount = max(
            0.0,
            reference
            - min(row["omega_m"] for row in rows),
        )

    elif reference < 0.0:
        overshoot_amount = max(
            0.0,
            reference
            - min(row["omega_m"] for row in rows),
        )

        overshoot_percent = (
            100.0 * overshoot_amount / abs(reference)
        )

        undershoot_amount = max(
            0.0,
            max(row["omega_m"] for row in rows)
            - reference,
        )

    else:
        overshoot_amount = math.nan
        overshoot_percent = math.nan
        undershoot_amount = math.nan

    # ========================================================
    # Tiempo de establecimiento
    #
    # Para referencias no nulas:
    #
    #   banda = 2 % de |reference|
    #
    # Para referencia cero:
    #
    #   banda absoluta = 0.4 rad/s
    #
    # Esto evita dividir por cero.
    # ========================================================

    if abs(reference) > 0.0:
        settling_band = 0.02 * abs(reference)
    else:
        settling_band = 0.4

    settling_time = math.nan

    for index, row in enumerate(rows):
        remaining = rows[index:]

        if all(
            abs(r["omega_m"] - reference)
            <= settling_band
            for r in remaining
        ):
            settling_time = row["t"] - start
            break

    # ========================================================
    # Valores máximos de corriente y par
    # ========================================================

    max_abs_iq_ref = max(
        abs(row["iq_ref"])
        for row in rows
    )

    max_abs_iq = max(
        abs(row["iq"])
        for row in rows
    )

    max_abs_te = max(
        abs(row["te"])
        for row in rows
    )

    max_abs_tf = max(
        abs(row["friction_torque"])
        for row in rows
    )

    return {
        "start_s": start,
        "end_s": end,
        "reference_rad_s": reference,
        "mae_rad_s": mae,
        "rmse_rad_s": rmse,
        "max_abs_error_rad_s": max_abs_error,
        "final_error_rad_s": final_error,
        "final_abs_error_rad_s": final_abs_error,
        "overshoot_amount_rad_s": overshoot_amount,
        "overshoot_percent": overshoot_percent,
        "undershoot_amount_rad_s": undershoot_amount,
        "settling_time_2pct_s": settling_time,
        "max_abs_iq_ref_A": max_abs_iq_ref,
        "max_abs_iq_A": max_abs_iq,
        "max_abs_te_Nm": max_abs_te,
        "max_abs_tf_Nm": max_abs_tf,
    }


# ============================================================
# COMPARACIÓN DE MÉTRICAS
# ============================================================

def build_comparison(
    base_history: list[dict[str, float]],
    friction_history: list[dict[str, float]],
) -> list[dict[str, float]]:
    """Calcula métricas de ambas plantas y sus diferencias."""

    rows = []

    for segment in SEGMENTS:
        base = segment_metrics(
            base_history,
            start=segment["start"],
            end=segment["end"],
            reference=segment["reference"],
        )

        friction = segment_metrics(
            friction_history,
            start=segment["start"],
            end=segment["end"],
            reference=segment["reference"],
        )

        rows.append(
            {
                "segment": segment["name"],
                "start_s": segment["start"],
                "end_s": segment["end"],
                "reference_rad_s": segment["reference"],

                "base_mae_rad_s": base["mae_rad_s"],
                "friction_mae_rad_s": friction["mae_rad_s"],
                "delta_mae_rad_s": (
                    friction["mae_rad_s"]
                    - base["mae_rad_s"]
                ),

                "base_rmse_rad_s": base["rmse_rad_s"],
                "friction_rmse_rad_s": friction["rmse_rad_s"],
                "delta_rmse_rad_s": (
                    friction["rmse_rad_s"]
                    - base["rmse_rad_s"]
                ),

                "base_max_abs_error_rad_s": (
                    base["max_abs_error_rad_s"]
                ),
                "friction_max_abs_error_rad_s": (
                    friction["max_abs_error_rad_s"]
                ),
                "delta_max_abs_error_rad_s": (
                    friction["max_abs_error_rad_s"]
                    - base["max_abs_error_rad_s"]
                ),

                "base_final_error_rad_s": (
                    base["final_error_rad_s"]
                ),
                "friction_final_error_rad_s": (
                    friction["final_error_rad_s"]
                ),

                "base_final_abs_error_rad_s": (
                    base["final_abs_error_rad_s"]
                ),
                "friction_final_abs_error_rad_s": (
                    friction["final_abs_error_rad_s"]
                ),
                "delta_final_abs_error_rad_s": (
                    friction["final_abs_error_rad_s"]
                    - base["final_abs_error_rad_s"]
                ),

                "base_overshoot_percent": (
                    base["overshoot_percent"]
                ),
                "friction_overshoot_percent": (
                    friction["overshoot_percent"]
                ),

                "base_settling_time_2pct_s": (
                    base["settling_time_2pct_s"]
                ),
                "friction_settling_time_2pct_s": (
                    friction["settling_time_2pct_s"]
                ),

                "base_max_abs_iq_ref_A": (
                    base["max_abs_iq_ref_A"]
                ),
                "friction_max_abs_iq_ref_A": (
                    friction["max_abs_iq_ref_A"]
                ),

                "base_max_abs_iq_A": (
                    base["max_abs_iq_A"]
                ),
                "friction_max_abs_iq_A": (
                    friction["max_abs_iq_A"]
                ),

                "base_max_abs_te_Nm": (
                    base["max_abs_te_Nm"]
                ),
                "friction_max_abs_te_Nm": (
                    friction["max_abs_te_Nm"]
                ),

                "friction_max_abs_tf_Nm": (
                    friction["max_abs_tf_Nm"]
                ),
            }
        )

    return rows


# ============================================================
# CSV DE TRAYECTORIA
# ============================================================

def write_trajectory_csv(
    base_history: list[dict[str, float]],
    friction_history: list[dict[str, float]],
    output_file: str,
) -> None:
    """Escribe ambas trayectorias en un CSV."""

    if len(base_history) != len(friction_history):
        raise RuntimeError(
            "Las trayectorias no tienen la misma longitud."
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
            base_history,
            friction_history,
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
    comparison: list[dict[str, float]],
    output_file: str,
) -> None:
    """Escribe las métricas comparativas."""

    if not comparison:
        raise RuntimeError("No hay métricas para escribir.")

    fieldnames = list(comparison[0].keys())

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(comparison)


# ============================================================
# IMPRESIÓN
# ============================================================

def print_comparison(
    comparison: list[dict[str, float]],
) -> None:
    """Imprime las métricas principales."""

    print()
    print("========================================")
    print(" MÉTRICAS POR TRANSICIÓN")
    print("========================================")

    for row in comparison:
        print()
        print(
            f"[{row['segment']}] "
            f"{row['start_s']:.3f} -> "
            f"{row['end_s']:.3f} s"
        )
        print(
            f"Referencia       = "
            f"{row['reference_rad_s']:.6f} rad/s"
        )

        print()
        print("MAE")
        print(
            f"  base           = "
            f"{row['base_mae_rad_s']:.9f}"
        )
        print(
            f"  fricción       = "
            f"{row['friction_mae_rad_s']:.9f}"
        )
        print(
            f"  delta          = "
            f"{row['delta_mae_rad_s']:.9f}"
        )

        print()
        print("RMSE")
        print(
            f"  base           = "
            f"{row['base_rmse_rad_s']:.9f}"
        )
        print(
            f"  fricción       = "
            f"{row['friction_rmse_rad_s']:.9f}"
        )
        print(
            f"  delta          = "
            f"{row['delta_rmse_rad_s']:.9f}"
        )

        print()
        print("Error final absoluto")
        print(
            f"  base           = "
            f"{row['base_final_abs_error_rad_s']:.9f}"
        )
        print(
            f"  fricción       = "
            f"{row['friction_final_abs_error_rad_s']:.9f}"
        )
        print(
            f"  delta          = "
            f"{row['delta_final_abs_error_rad_s']:.9f}"
        )

        print()
        print("Sobreimpulso")
        print(
            f"  base           = "
            f"{row['base_overshoot_percent']}"
        )
        print(
            f"  fricción       = "
            f"{row['friction_overshoot_percent']}"
        )

        print()
        print("Corriente |iq_ref| máxima")
        print(
            f"  base           = "
            f"{row['base_max_abs_iq_ref_A']:.9f} A"
        )
        print(
            f"  fricción       = "
            f"{row['friction_max_abs_iq_ref_A']:.9f} A"
        )

        print()
        print("Par |Te| máximo")
        print(
            f"  base           = "
            f"{row['base_max_abs_te_Nm']:.9f} N*m"
        )
        print(
            f"  fricción       = "
            f"{row['friction_max_abs_te_Nm']:.9f} N*m"
        )

        print()
        print("Par de fricción |Tf| máximo")
        print(
            f"  fricción       = "
            f"{row['friction_max_abs_tf_Nm']:.9f} N*m"
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("========================================")
    print(" F1.4 — BAJA VELOCIDAD Y REVERSIÓN")
    print("========================================")
    print(f"dt          = {DT:.8f} s")
    print(f"duration    = {T_END:.6f} s")
    print(f"steps       = {STEPS}")
    print(f"id_ref      = {ID_REF:.6f} A")
    print(f"T_load      = {T_LOAD:.6f} N*m")

    print()
    print("REFERENCE PROFILE")
    print("----------------------------------------")

    for t0, value in REFERENCE_LEVELS:
        print(
            f"t = {t0:.3f} s -> "
            f"omega_ref = {value:.6f} rad/s"
        )

    print()
    print("FRICTION SCENARIO")
    print("----------------------------------------")
    print(
        f"Tc          = "
        f"{FRICTION_PARAMETERS.tc:.6f} N*m"
    )
    print(
        f"Ts          = "
        f"{FRICTION_PARAMETERS.ts:.6f} N*m"
    )
    print(
        f"omega_s     = "
        f"{FRICTION_PARAMETERS.omega_s:.6f} rad/s"
    )
    print(
        f"delta       = "
        f"{FRICTION_PARAMETERS.delta:.6f}"
    )
    print(
        f"B           = "
        f"{FRICTION_PARAMETERS.b:.6f} "
        f"N*m*s/rad"
    )

    # --------------------------------------------------------
    # A — planta sin fricción
    # --------------------------------------------------------

    base_plant = PMSMBase()

    base_history = run_case(
        plant=base_plant,
        friction_enabled=False,
    )

    # --------------------------------------------------------
    # B — planta con fricción
    # --------------------------------------------------------

    friction = StribeckFriction(
        FRICTION_PARAMETERS
    )

    friction_plant = PMSMWithFriction(
        friction=friction,
    )

    friction_history = run_case(
        plant=friction_plant,
        friction_enabled=True,
    )

    # --------------------------------------------------------
    # Métricas
    # --------------------------------------------------------

    comparison = build_comparison(
        base_history=base_history,
        friction_history=friction_history,
    )

    # --------------------------------------------------------
    # Archivos
    # --------------------------------------------------------

    trajectory_file = (
        "experiments/f1_4_low_speed_reversal_friction.csv"
    )

    metrics_file = (
        "experiments/f1_4_low_speed_reversal_metrics.csv"
    )

    write_trajectory_csv(
        base_history=base_history,
        friction_history=friction_history,
        output_file=trajectory_file,
    )

    write_metrics_csv(
        comparison=comparison,
        output_file=metrics_file,
    )

    # --------------------------------------------------------
    # Resultados
    # --------------------------------------------------------

    print_comparison(comparison)

    print()
    print("========================================")
    print(" SALIDA")
    print("========================================")
    print(f"CSV trayectoria = {trajectory_file}")
    print(f"CSV métricas    = {metrics_file}")


if __name__ == "__main__":
    main()
