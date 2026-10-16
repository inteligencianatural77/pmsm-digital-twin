from __future__ import annotations

import csv
from pathlib import Path


# ============================================================================
# J3.1 — CRITERIO REPRODUCIBLE PARA GENERACIÓN DE ETIQUETAS ANFIS
#
# Fuente:
#   B2.5 — experiments/b2_5_parameter_sweep_metrics.csv
#
# Propósito:
#   Caracterizar las configuraciones PI a partir de los resultados existentes
#   de B2.5, sin convertir métricas episódicas en etiquetas instantáneas.
#
# Importante:
#   - No genera nuevas simulaciones.
#   - No modifica ningún resultado de B2.5.
#   - No declara una configuración como "óptima".
#   - B2.5 registra iq_ref_max_A, no la corriente efectiva iq.
#   - Por tanto, J3.1 NO aplica el límite físico de 79.5 A a iq.
#   - La verificación de iq requiere trayectorias que B2.5 no conserva.
# ============================================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT / "experiments" / "b2_5_parameter_sweep_metrics.csv"

OUTPUT_DIR = ROOT / "experiments" / "j3_1_label_criteria"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, str], name: str) -> float:
    value = row.get(name)

    if value is None or value == "":
        raise KeyError(
            f"No se encontró la columna '{name}'. "
            f"Columnas disponibles: {list(row)}"
        )

    return float(value)


def normalize_row(row: dict[str, str]) -> dict:
    return {
        "scenario": row["scenario"],
        "transition": row["transition"],
        "start_s": as_float(row, "start_s"),
        "end_s": as_float(row, "end_s"),
        "reference_rad_s": as_float(row, "reference_rad_s"),

        "kp_factor": as_float(row, "kp_factor"),
        "ki_factor": as_float(row, "ki_factor"),
        "kp": as_float(row, "kp"),
        "ki": as_float(row, "ki"),

        "mae": as_float(row, "mae_rad_s"),
        "rmse": as_float(row, "rmse_rad_s"),
        "final_abs_error": as_float(row, "final_abs_error_rad_s"),
        "max_abs_error": as_float(row, "max_abs_error_rad_s"),
        "settling_time": as_float(row, "settling_time_s"),
        "overshoot_percent": as_float(row, "overshoot_percent"),

        # IMPORTANTE:
        # B2.5 registra la referencia de corriente, no la corriente efectiva.
        "iq_ref_max": abs(as_float(row, "iq_ref_max_A")),

        "te_max": abs(as_float(row, "te_max_Nm")),
        "tf_max": abs(as_float(row, "tf_max_Nm")),
    }


def write_csv(
    path: Path,
    rows: list[dict],
    fields: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dominates_configuration(a: dict, b: dict) -> bool:
    """
    Dominancia entre configuraciones agregadas de B2.5.

    Objetivos, todos a minimizar:

        mean_mae
        mean_rmse
        max_iq_ref

    max_iq_ref corresponde a la máxima referencia de corriente
    iq_ref generada por el lazo de velocidad.

    No corresponde a la corriente medida iq y, por tanto,
    no constituye una validación del límite físico de corriente.
    """

    a_values = (
        a["mean_mae"],
        a["mean_rmse"],
        a["max_iq_ref"],
    )

    b_values = (
        b["mean_mae"],
        b["mean_rmse"],
        b["max_iq_ref"],
    )

    no_worse = all(
        x <= y
        for x, y in zip(a_values, b_values)
    )

    strictly_better = any(
        x < y
        for x, y in zip(a_values, b_values)
    )

    return no_worse and strictly_better


def dominates_evaluation(a: dict, b: dict) -> bool:
    """
    Dominancia entre evaluaciones individuales de B2.5.

    Objetivos, todos a minimizar:

        mae
        rmse
        iq_ref_max

    Aquí cada fila corresponde a una combinación concreta de:

        escenario + transición + configuración Kp/Ki.

    iq_ref_max sigue siendo la referencia máxima de corriente,
    no la corriente medida iq.
    """

    a_values = (
        a["mae"],
        a["rmse"],
        a["iq_ref_max"],
    )

    b_values = (
        b["mae"],
        b["rmse"],
        b["iq_ref_max"],
    )

    no_worse = all(
        x <= y
        for x, y in zip(a_values, b_values)
    )

    strictly_better = any(
        x < y
        for x, y in zip(a_values, b_values)
    )

    return no_worse and strictly_better


def pareto_front(
    rows: list[dict],
    dominance_function,
) -> list[dict]:
    """
    Calcula el frente de Pareto utilizando explícitamente
    la función de dominancia correspondiente al nivel de análisis.

    Esto evita mezclar:

        - métricas agregadas por configuración, y
        - métricas de evaluaciones individuales.

    La función de dominancia se proporciona explícitamente
    mediante dominance_function.
    """

    front = []

    for candidate in rows:
        dominated = False

        for other in rows:
            if other is candidate:
                continue

            if dominance_function(other, candidate):
                dominated = True
                break

        if not dominated:
            front.append(candidate)

    return front


def main() -> None:
    print("=" * 72)
    print(" J3.1 — CRITERIO DE ETIQUETAS ANFIS")
    print("=" * 72)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el resultado B2.5 esperado:\n{INPUT_PATH}"
        )

    raw_rows = read_csv(INPUT_PATH)

    print(f"input = {INPUT_PATH}")
    print(f"raw rows = {len(raw_rows)}")

    if len(raw_rows) != 784:
        raise ValueError(
            f"Se esperaban 784 evaluaciones B2.5 según el ensayo registrado; "
            f"se encontraron {len(raw_rows)}."
        )

    rows = [normalize_row(row) for row in raw_rows]

    # ------------------------------------------------------------------------
    # Validación básica.
    # ------------------------------------------------------------------------

    numeric_fields = [
        "start_s",
        "end_s",
        "reference_rad_s",
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "mae",
        "rmse",
        "final_abs_error",
        "max_abs_error",
        "settling_time",
        "overshoot_percent",
        "iq_ref_max",
        "te_max",
        "tf_max",
    ]

    # Algunas métricas derivadas pueden no estar definidas para
    # determinadas trayectorias.
    #
    # Por ejemplo:
    #   - settling_time puede ser NaN si no se alcanza el criterio de
    #     establecimiento dentro de la ventana experimental.
    #   - overshoot_percent puede ser NaN cuando no existe un sobreimpulso
    #     definible para la transición considerada.
    #
    # Estos NaN conservan información experimental y NO se convierten
    # artificialmente en cero.
    #
    # Las métricas fundamentales utilizadas para el frente Pareto sí deben
    # ser finitas.
    nullable_fields = {
        "settling_time",
        "overshoot_percent",
    }

    for index, row in enumerate(rows):
        for field in numeric_fields:
            value = row[field]

            if not isinstance(value, float):
                raise TypeError(
                    f"Fila {index}: {field} no es float."
                )

            if value != value:
                if field not in nullable_fields:
                    raise ValueError(
                        f"Fila {index}: {field} contiene NaN."
                    )

    # ------------------------------------------------------------------------
    # Catálogo de configuraciones.
    #
    # Una configuración se identifica por sus factores Kp/Ki.
    # Las métricas agregadas aquí son descriptivas del conjunto B2.5.
    # ------------------------------------------------------------------------

    grouped: dict[tuple[float, float], list[dict]] = {}

    for row in rows:
        key = (
            row["kp_factor"],
            row["ki_factor"],
        )
        grouped.setdefault(key, []).append(row)

    configuration_rows = []

    for (kp_factor, ki_factor), group in sorted(grouped.items()):
        mean_mae = sum(
            row["mae"] for row in group
        ) / len(group)

        mean_rmse = sum(
            row["rmse"] for row in group
        ) / len(group)

        max_iq_ref = max(
            row["iq_ref_max"] for row in group
        )

        mean_iq_ref = sum(
            row["iq_ref_max"] for row in group
        ) / len(group)

        configuration_rows.append(
            {
                "kp_factor": kp_factor,
                "ki_factor": ki_factor,
                "kp": group[0]["kp"],
                "ki": group[0]["ki"],
                "evaluations": len(group),
                "mean_mae": mean_mae,
                "mean_rmse": mean_rmse,
                "max_iq_ref": max_iq_ref,
                "mean_iq_ref": mean_iq_ref,
            }
        )

    # ------------------------------------------------------------------------
    # Frente Pareto global.
    #
    # Esto es un frente de desempeño respecto a:
    #   MAE, RMSE e iq_ref_max.
    #
    # NO es un frente físico de corriente.
    # ------------------------------------------------------------------------

    global_front = pareto_front(
        configuration_rows,
        dominates_configuration,
    )

    global_front_keys = {
        (
            row["kp_factor"],
            row["ki_factor"],
        )
        for row in global_front
    }

    for row in configuration_rows:
        row["global_pareto"] = int(
            (
                row["kp_factor"],
                row["ki_factor"],
            )
            in global_front_keys
        )

    # ------------------------------------------------------------------------
    # Frente Pareto por escenario + transición.
    #
    # Aquí se conserva la granularidad experimental original de B2.5.
    # ------------------------------------------------------------------------

    condition_groups: dict[
        tuple[str, str],
        list[dict]
    ] = {}

    for row in rows:
        key = (
            row["scenario"],
            row["transition"],
        )

        condition_groups.setdefault(key, []).append(row)

    condition_front_rows = []

    for (scenario, transition), group in sorted(
        condition_groups.items()
    ):
        front = pareto_front(
            group,
            dominates_evaluation,
        )

        for row in front:
            condition_front_rows.append(
                {
                    "scenario": scenario,
                    "transition": transition,
                    "kp_factor": row["kp_factor"],
                    "ki_factor": row["ki_factor"],
                    "kp": row["kp"],
                    "ki": row["ki"],
                    "mae": row["mae"],
                    "rmse": row["rmse"],
                    "final_abs_error": row["final_abs_error"],
                    "max_abs_error": row["max_abs_error"],
                    "settling_time": row["settling_time"],
                    "overshoot_percent": row["overshoot_percent"],
                    "iq_ref_max": row["iq_ref_max"],
                    "te_max": row["te_max"],
                    "tf_max": row["tf_max"],
                }
            )

    # ------------------------------------------------------------------------
    # Exportación.
    # ------------------------------------------------------------------------

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(
        OUTPUT_DIR / "j3_1_configuration_catalog.csv",
        configuration_rows,
        [
            "kp_factor",
            "ki_factor",
            "kp",
            "ki",
            "evaluations",
            "mean_mae",
            "mean_rmse",
            "max_iq_ref",
            "mean_iq_ref",
            "global_pareto",
        ],
    )

    write_csv(
        OUTPUT_DIR / "j3_1_global_pareto.csv",
        global_front,
        [
            "kp_factor",
            "ki_factor",
            "kp",
            "ki",
            "evaluations",
            "mean_mae",
            "mean_rmse",
            "max_iq_ref",
            "mean_iq_ref",
            "global_pareto",
        ],
    )

    write_csv(
        OUTPUT_DIR / "j3_1_condition_pareto.csv",
        condition_front_rows,
        [
            "scenario",
            "transition",
            "kp_factor",
            "ki_factor",
            "kp",
            "ki",
            "mae",
            "rmse",
            "final_abs_error",
            "max_abs_error",
            "settling_time",
            "overshoot_percent",
            "iq_ref_max",
            "te_max",
            "tf_max",
        ],
    )

    # ------------------------------------------------------------------------
    # Reporte.
    # ------------------------------------------------------------------------

    print()
    print("CONFIGURATION CATALOG")
    print("---------------------")
    print(f"tested configurations = {len(configuration_rows)}")
    print(f"global Pareto configurations = {len(global_front)}")

    print()
    print("GLOBAL PARETO CONFIGURATIONS")
    print("----------------------------")

    for row in sorted(
        global_front,
        key=lambda x: (
            x["kp_factor"],
            x["ki_factor"],
        ),
    ):
        print(
            f"Kp_factor={row['kp_factor']:.5f} "
            f"Ki_factor={row['ki_factor']:.5f} "
            f"MAE={row['mean_mae']:.6f} "
            f"RMSE={row['mean_rmse']:.6f} "
            f"max|iq_ref|={row['max_iq_ref']:.6f} A"
        )

    print()
    print("CONDITIONED PARETO")
    print("------------------")
    print(
        f"scenario-transition conditions = "
        f"{len(condition_groups)}"
    )
    print(
        f"Pareto evaluations exported = "
        f"{len(condition_front_rows)}"
    )

    print()
    print("CURRENT LIMIT STATUS")
    print("--------------------")
    print(
        "Physical iq limit = 79.5 A: "
        "NOT EVALUATED BY THIS J3.1 DATASET"
    )
    print(
        "Available quantity = iq_ref_max_A "
        "(reference current generated by speed PI)"
    )

    print()
    print("OUTPUTS")
    print("-------")
    print(
        OUTPUT_DIR / "j3_1_configuration_catalog.csv"
    )
    print(
        OUTPUT_DIR / "j3_1_global_pareto.csv"
    )
    print(
        OUTPUT_DIR / "j3_1_condition_pareto.csv"
    )

    print()
    print("=" * 72)
    print(" J3.1 — ANÁLISIS COMPLETADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
