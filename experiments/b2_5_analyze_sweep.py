from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

METRICS_FILE = ROOT / "experiments" / "b2_5_parameter_sweep_metrics.csv"
CONFIG_FILE = ROOT / "experiments" / "b2_5_parameter_sweep_config.csv"

OUTPUT_DIR = ROOT / "experiments" / "b2_5_analysis"


EXPECTED_SCENARIOS = {
    "no_friction",
    "friction_base",
    "friction_medium",
    "friction_high",
}

EXPECTED_TRANSITIONS = {
    "0_to_plus20",
    "plus20_to_zero",
    "zero_to_minus20",
    "minus20_to_zero",
}


def header(title: str) -> None:
    print()
    print("=" * 72)
    print(f" {title}")
    print("=" * 72)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def numeric(
    row: dict[str, str],
    key: str,
) -> float:
    value = row.get(key, "")

    if value is None or value == "":
        return math.nan

    try:
        return float(value)
    except ValueError:
        return math.nan


def unique_values(
    rows: list[dict[str, str]],
    key: str,
) -> set[str]:
    return {
        row[key]
        for row in rows
        if key in row
    }


def group_by(
    rows: list[dict[str, str]],
    keys: list[str],
) -> dict[tuple[str, ...], list[dict[str, str]]]:
    groups: dict[
        tuple[str, ...],
        list[dict[str, str]]
    ] = {}

    for row in rows:
        group_key = tuple(
            row.get(key, "")
            for key in keys
        )

        groups.setdefault(
            group_key,
            [],
        ).append(row)

    return groups


def values(
    rows: list[dict[str, str]],
    key: str,
) -> np.ndarray:
    return np.asarray(
        [
            numeric(row, key)
            for row in rows
        ],
        dtype=float,
    )


def finite_values(
    rows: list[dict[str, str]],
    key: str,
) -> np.ndarray:
    data = values(rows, key)

    return data[np.isfinite(data)]


def mean(
    rows: list[dict[str, str]],
    key: str,
) -> float:
    data = finite_values(rows, key)

    if len(data) == 0:
        return math.nan

    return float(np.mean(data))


def median(
    rows: list[dict[str, str]],
    key: str,
) -> float:
    data = finite_values(rows, key)

    if len(data) == 0:
        return math.nan

    return float(np.median(data))


def minimum(
    rows: list[dict[str, str]],
    key: str,
) -> float:
    data = finite_values(rows, key)

    if len(data) == 0:
        return math.nan

    return float(np.min(data))


def maximum(
    rows: list[dict[str, str]],
    key: str,
) -> float:
    data = finite_values(rows, key)

    if len(data) == 0:
        return math.nan

    return float(np.max(data))


def std(
    rows: list[dict[str, str]],
    key: str,
) -> float:
    data = finite_values(rows, key)

    if len(data) < 2:
        return math.nan

    return float(np.std(data, ddof=1))


def quantile(
    rows: list[dict[str, str]],
    key: str,
    q: float,
) -> float:
    data = finite_values(rows, key)

    if len(data) == 0:
        return math.nan

    return float(np.quantile(data, q))


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    metrics: list[dict[str, str]],
    config: list[dict[str, str]],
) -> None:
    header("VALIDACIÓN DE ENTRADAS")

    print(f"Métricas : {METRICS_FILE}")
    print(f"Config   : {CONFIG_FILE}")
    print(f"Filas métricas : {len(metrics)}")
    print(f"Filas config   : {len(config)}")

    if len(config) != 196:
        raise ValueError(
            f"Se esperaban 196 configuraciones; "
            f"se encontraron {len(config)}."
        )

    if len(metrics) != 784:
        raise ValueError(
            f"Se esperaban 784 métricas; "
            f"se encontraron {len(metrics)}."
        )

    scenarios = unique_values(
        metrics,
        "scenario",
    )

    transitions = unique_values(
        metrics,
        "transition",
    )

    print()
    print(
        "Escenarios:",
        sorted(scenarios),
    )

    print(
        "Transiciones:",
        sorted(transitions),
    )

    missing_scenarios = (
        EXPECTED_SCENARIOS - scenarios
    )

    missing_transitions = (
        EXPECTED_TRANSITIONS - transitions
    )

    if missing_scenarios:
        raise ValueError(
            f"Faltan escenarios: "
            f"{sorted(missing_scenarios)}"
        )

    if missing_transitions:
        raise ValueError(
            f"Faltan transiciones: "
            f"{sorted(missing_transitions)}"
        )

    config_keys = {
        (
            row["scenario"],
            row["kp_factor"],
            row["ki_factor"],
        )
        for row in config
    }

    if len(config_keys) != 196:
        raise ValueError(
            "La tabla de configuraciones "
            "contiene combinaciones duplicadas."
        )

    metric_keys = {
        (
            row["scenario"],
            row["kp_factor"],
            row["ki_factor"],
            row["transition"],
        )
        for row in metrics
    }

    if len(metric_keys) != 784:
        raise ValueError(
            "La tabla de métricas contiene "
            "combinaciones duplicadas."
        )

    print()
    print("OK: 196 configuraciones.")
    print("OK: 784 filas métricas.")
    print("OK: 4 escenarios.")
    print("OK: 4 transiciones.")
    print("OK: sin duplicados.")


def numeric_integrity(
    metrics: list[dict[str, str]],
) -> None:
    header("1 — INTEGRIDAD NUMÉRICA")

    columns = [
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "mae_rad_s",
        "rmse_rad_s",
        "final_abs_error_rad_s",
        "max_abs_error_rad_s",
        "settling_time_s",
        "overshoot_percent",
        "iq_ref_max_A",
        "te_max_Nm",
        "tf_max_Nm",
    ]

    result = []

    for column in columns:
        data = values(metrics, column)
        finite = np.isfinite(data)

        result.append(
            {
                "variable": column,
                "filas": len(data),
                "finite": int(np.sum(finite)),
                "nonfinite": int(np.sum(~finite)),
                "min": minimum(metrics, column),
                "max": maximum(metrics, column),
                "mean": mean(metrics, column),
                "median": median(metrics, column),
            }
        )

    for row in result:
        print(
            f"{row['variable']:22s} "
            f"finite={row['finite']:4d} "
            f"nonfinite={row['nonfinite']:4d} "
            f"min={row['min']:.9g} "
            f"max={row['max']:.9g}"
        )

    write_csv(
        OUTPUT_DIR / "numeric_integrity.csv",
        list(result[0].keys()),
        result,
    )


def global_statistics(
    metrics: list[dict[str, str]],
) -> None:
    header("2 — ESTADÍSTICA GLOBAL")

    columns = [
        "mae_rad_s",
        "rmse_rad_s",
        "final_abs_error_rad_s",
        "max_abs_error_rad_s",
        "settling_time_s",
        "overshoot_percent",
        "iq_ref_max_A",
        "te_max_Nm",
        "tf_max_Nm",
    ]

    result = []

    for column in columns:
        result.append(
            {
                "metric": column,
                "count": len(
                    finite_values(metrics, column)
                ),
                "min": minimum(metrics, column),
                "q25": quantile(
                    metrics,
                    column,
                    0.25,
                ),
                "median": median(metrics, column),
                "q75": quantile(
                    metrics,
                    column,
                    0.75,
                ),
                "max": maximum(metrics, column),
                "mean": mean(metrics, column),
                "std": std(metrics, column),
            }
        )

    for row in result:
        print(
            f"{row['metric']:22s} "
            f"mean={row['mean']:.9g} "
            f"median={row['median']:.9g} "
            f"min={row['min']:.9g} "
            f"max={row['max']:.9g}"
        )

    write_csv(
        OUTPUT_DIR / "global_statistics.csv",
        list(result[0].keys()),
        result,
    )


def scenario_analysis(
    metrics: list[dict[str, str]],
) -> None:
    header("3 — CARACTERIZACIÓN POR ESCENARIO")

    groups = group_by(
        metrics,
        ["scenario"],
    )

    result = []

    for key, rows in sorted(groups.items()):
        scenario = key[0]

        result.append(
            {
                "scenario": scenario,
                "mae_mean": mean(rows, "mae_rad_s"),
                "mae_median": median(rows, "mae_rad_s"),
                "rmse_mean": mean(rows, "rmse_rad_s"),
                "rmse_median": median(rows, "rmse_rad_s"),
                "final_error_mean": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "final_error_median": median(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
                "tf_max": maximum(
                    rows,
                    "tf_max_Nm",
                ),
            }
        )

    for row in result:
        print(
            f"{row['scenario']:18s} "
            f"MAE={row['mae_mean']:.6f} "
            f"RMSE={row['rmse_mean']:.6f} "
            f"|e_f|={row['final_error_mean']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "scenario_summary.csv",
        list(result[0].keys()),
        result,
    )


def transition_analysis(
    metrics: list[dict[str, str]],
) -> None:
    header("4 — CARACTERIZACIÓN POR TRANSICIÓN")

    groups = group_by(
        metrics,
        ["transition"],
    )

    result = []

    for key, rows in sorted(groups.items()):
        result.append(
            {
                "transition": key[0],
                "mae_mean": mean(rows, "mae_rad_s"),
                "rmse_mean": mean(rows, "rmse_rad_s"),
                "final_error_mean": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "final_error_median": median(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
                "tf_max": maximum(
                    rows,
                    "tf_max_Nm",
                ),
            }
        )

    for row in result:
        print(
            f"{row['transition']:20s} "
            f"MAE={row['mae_mean']:.6f} "
            f"RMSE={row['rmse_mean']:.6f} "
            f"|e_f|={row['final_error_mean']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "transition_summary.csv",
        list(result[0].keys()),
        result,
    )


def kp_sensitivity(
    metrics: list[dict[str, str]],
) -> None:
    header("5 — SENSIBILIDAD RESPECTO A Kp")

    groups = group_by(
        metrics,
        ["scenario", "kp_factor"],
    )

    result = []

    for key, rows in sorted(
        groups.items(),
        key=lambda item: (
            item[0][0],
            float(item[0][1]),
        ),
    ):
        result.append(
            {
                "scenario": key[0],
                "kp_factor": key[1],
                "mae_mean": mean(rows, "mae_rad_s"),
                "rmse_mean": mean(rows, "rmse_rad_s"),
                "final_error_mean": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "final_error_max": maximum(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
            }
        )

    for row in result:
        print(
            f"{row['scenario']:18s} "
            f"Kp_factor={float(row['kp_factor']):.5f} "
            f"MAE={row['mae_mean']:.6f} "
            f"RMSE={row['rmse_mean']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "sensitivity_kp.csv",
        list(result[0].keys()),
        result,
    )


def ki_sensitivity(
    metrics: list[dict[str, str]],
) -> None:
    header("6 — SENSIBILIDAD RESPECTO A Ki")

    groups = group_by(
        metrics,
        ["scenario", "ki_factor"],
    )

    result = []

    for key, rows in sorted(
        groups.items(),
        key=lambda item: (
            item[0][0],
            float(item[0][1]),
        ),
    ):
        result.append(
            {
                "scenario": key[0],
                "ki_factor": key[1],
                "mae_mean": mean(rows, "mae_rad_s"),
                "rmse_mean": mean(rows, "rmse_rad_s"),
                "final_error_mean": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "final_error_max": maximum(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
            }
        )

    for row in result:
        print(
            f"{row['scenario']:18s} "
            f"Ki_factor={float(row['ki_factor']):.5f} "
            f"MAE={row['mae_mean']:.6f} "
            f"RMSE={row['rmse_mean']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "sensitivity_ki.csv",
        list(result[0].keys()),
        result,
    )


def generate_matrices(
    metrics: list[dict[str, str]],
) -> None:
    header("7 — MATRICES Kp-Ki")

    groups = group_by(
        metrics,
        [
            "scenario",
            "kp_factor",
            "ki_factor",
        ],
    )

    scenarios = sorted(
        {
            key[0]
            for key in groups
        }
    )

    matrix_metrics = [
        "mae_rad_s",
        "rmse_rad_s",
        "final_abs_error_rad_s",
        "iq_ref_max_A",
        "te_max_Nm",
    ]

    for scenario in scenarios:
        for metric in matrix_metrics:
            kp_values = sorted(
                {
                    float(key[1])
                    for key in groups
                    if key[0] == scenario
                }
            )

            ki_values = sorted(
                {
                    float(key[2])
                    for key in groups
                    if key[0] == scenario
                }
            )

            path = (
                OUTPUT_DIR
                / f"matrix_{scenario}_{metric}.csv"
            )

            with path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:
                writer = csv.writer(file)

                writer.writerow(
                    [
                        "kp_factor"
                    ]
                    + [
                        f"{value:.5f}"
                        for value in ki_values
                    ]
                )

                for kp in kp_values:
                    row = [f"{kp:.5f}"]

                    for ki in ki_values:
                        key = (
                            scenario,
                            f"{kp:g}",
                            f"{ki:g}",
                        )

                        matching = groups.get(
                            key,
                            [],
                        )

                        if matching:
                            row.append(
                                f"{mean(matching, metric):.9g}"
                            )
                        else:
                            row.append("nan")

                    writer.writerow(row)

            print(path.name)


def extreme_analysis(
    metrics: list[dict[str, str]],
) -> None:
    header("8 — CONFIGURACIONES EXTREMAS")

    columns = [
        "mae_rad_s",
        "rmse_rad_s",
        "final_abs_error_rad_s",
        "max_abs_error_rad_s",
        "iq_ref_max_A",
        "te_max_Nm",
    ]

    for column in columns:
        ranked = sorted(
            metrics,
            key=lambda row: (
                numeric(row, column)
                if math.isfinite(
                    numeric(row, column)
                )
                else -math.inf
            ),
            reverse=True,
        )

        selected = ranked[:10]

        print()
        print(f"Mayor {column}:")

        for row in selected:
            print(
                f"  {row['scenario']:18s} "
                f"{row['transition']:20s} "
                f"Kp_f={float(row['kp_factor']):.5f} "
                f"Ki_f={float(row['ki_factor']):.5f} "
                f"{column}="
                f"{numeric(row, column):.9g}"
            )

        fields = [
            "scenario",
            "transition",
            "kp_factor",
            "ki_factor",
            "kp",
            "ki",
            column,
        ]

        write_csv(
            OUTPUT_DIR
            / f"extreme_high_{column}.csv",
            fields,
            [
                {
                    field: row[field]
                    for field in fields
                }
                for row in selected
            ],
        )


def candidate_analysis(
    metrics: list[dict[str, str]],
) -> None:
    header(
        "9 — FILTRO DE INSPECCIÓN DE CANDIDATOS"
    )

    # Filtros de inspección.
    #
    # NO son límites físicos del Siemens 1FT7087.
    # NO constituyen todavía las etiquetas ANFIS.

    MAE_LIMIT = 1.0
    RMSE_LIMIT = 3.0
    FINAL_ERROR_LIMIT = 0.5

    selected = []

    for row in metrics:
        mae = numeric(row, "mae_rad_s")
        rmse = numeric(row, "rmse_rad_s")
        final_error = numeric(
            row,
            "final_abs_error_rad_s",
        )

        if (
            math.isfinite(mae)
            and math.isfinite(rmse)
            and math.isfinite(final_error)
            and mae <= MAE_LIMIT
            and rmse <= RMSE_LIMIT
            and final_error <= FINAL_ERROR_LIMIT
        ):
            selected.append(row)

    print(
        f"MAE <= {MAE_LIMIT}"
    )
    print(
        f"RMSE <= {RMSE_LIMIT}"
    )
    print(
        f"|error final| <= {FINAL_ERROR_LIMIT}"
    )

    print()
    print(
        f"Filas seleccionadas: "
        f"{len(selected)} / {len(metrics)}"
    )

    if selected:
        fields = list(selected[0].keys())

        write_csv(
            OUTPUT_DIR / "candidate_rows.csv",
            fields,
            selected,
        )
    else:
        write_csv(
            OUTPUT_DIR / "candidate_rows.csv",
            list(metrics[0].keys()),
            [],
        )

        print(
            "No hay filas bajo los filtros."
        )

        return

    groups = group_by(
        selected,
        [
            "scenario",
            "kp_factor",
            "ki_factor",
            "kp",
            "ki",
        ],
    )

    result = []

    for key, rows in groups.items():
        result.append(
            {
                "scenario": key[0],
                "kp_factor": key[1],
                "ki_factor": key[2],
                "kp": key[3],
                "ki": key[4],
                "transitions_pass": len(
                    {
                        row["transition"]
                        for row in rows
                    }
                ),
                "mae_mean": mean(rows, "mae_rad_s"),
                "rmse_mean": mean(rows, "rmse_rad_s"),
                "final_error_mean": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
            }
        )

    result.sort(
        key=lambda row: (
            row["scenario"],
            -row["transitions_pass"],
            row["mae_mean"],
        )
    )

    print()
    print(
        "Primeras configuraciones para inspección:"
    )

    for row in result[:30]:
        print(
            f"{row['scenario']:18s} "
            f"Kp={float(row['kp']):.6f} "
            f"Ki={float(row['ki']):.6f} "
            f"trans={row['transitions_pass']} "
            f"MAE={row['mae_mean']:.6f} "
            f"RMSE={row['rmse_mean']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "candidate_configurations.csv",
        list(result[0].keys()),
        result,
    )


def friction_analysis(
    metrics: list[dict[str, str]],
) -> None:
    header(
        "10 — EFECTO DEL ESCENARIO DE FRICCIÓN"
    )

    groups = group_by(
        metrics,
        [
            "scenario",
            "transition",
        ],
    )

    result = []

    for key, rows in sorted(groups.items()):
        result.append(
            {
                "scenario": key[0],
                "transition": key[1],
                "mae_rad_s": mean(rows, "mae_rad_s"),
                "rmse_rad_s": mean(rows, "rmse_rad_s"),
                "final_abs_error_rad_s": mean(
                    rows,
                    "final_abs_error_rad_s",
                ),
                "iq_ref_max": maximum(
                    rows,
                    "iq_ref_max_A",
                ),
                "te_max": maximum(
                    rows,
                    "te_max_Nm",
                ),
                "tf_max": maximum(
                    rows,
                    "tf_max_Nm",
                ),
            }
        )

    for row in result:
        print(
            f"{row['scenario']:18s} "
            f"{row['transition']:20s} "
            f"MAE={row['mae_rad_s']:.6f} "
            f"RMSE={row['rmse_rad_s']:.6f} "
            f"|e_f|={row['final_abs_error_rad_s']:.6f}"
        )

    write_csv(
        OUTPUT_DIR / "friction_effect.csv",
        list(result[0].keys()),
        result,
    )


def master_table(
    metrics: list[dict[str, str]],
) -> None:
    header("11 — TABLA MAESTRA")

    fields = [
        "scenario",
        "transition",
        "kp_factor",
        "ki_factor",
        "kp",
        "ki",
        "mae_rad_s",
        "rmse_rad_s",
        "final_abs_error_rad_s",
        "max_abs_error_rad_s",
        "settling_time_s",
        "overshoot_percent",
        "iq_ref_max_A",
        "te_max_Nm",
        "tf_max_Nm",
    ]

    result = sorted(
        metrics,
        key=lambda row: (
            row["scenario"],
            float(row["kp_factor"]),
            float(row["ki_factor"]),
            row["transition"],
        ),
    )

    write_csv(
        OUTPUT_DIR / "master_analysis_table.csv",
        fields,
        [
            {
                field: row[field]
                for field in fields
            }
            for row in result
        ],
    )

    print(
        OUTPUT_DIR / "master_analysis_table.csv"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics = read_csv(
        METRICS_FILE
    )

    config = read_csv(
        CONFIG_FILE
    )

    validate_inputs(
        metrics,
        config,
    )

    numeric_integrity(
        metrics
    )

    global_statistics(
        metrics
    )

    scenario_analysis(
        metrics
    )

    transition_analysis(
        metrics
    )

    kp_sensitivity(
        metrics
    )

    ki_sensitivity(
        metrics
    )

    generate_matrices(
        metrics
    )

    extreme_analysis(
        metrics
    )

    candidate_analysis(
        metrics
    )

    friction_analysis(
        metrics
    )

    master_table(
        metrics
    )

    header(
        "ANÁLISIS B2.5 COMPLETADO"
    )

    print(
        f"Resultados guardados en:\n"
        f"{OUTPUT_DIR}"
    )

    print()
    print(
        "El análisis caracteriza "
        "el barrido completo."
    )

    print(
        "No determina todavía "
        "Kp/Ki óptimos."
    )

    print(
        "No genera todavía "
        "etiquetas ANFIS."
    )


if __name__ == "__main__":
    main()
