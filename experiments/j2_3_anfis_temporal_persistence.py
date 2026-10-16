from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


INPUT_TRAJECTORIES = Path(
    "experiments/j1_anfis_analysis/j1_temporal_trajectories.csv"
)

INPUT_REGIONS = Path(
    "experiments/j2_1_anfis_intra_candidate/"
    "j2_1_observable_regions.csv"
)

OUTPUT_DIR = Path(
    "experiments/j2_3_anfis_temporal_persistence"
)

ERROR_BIN = 0.10
DELTA_ERROR_BIN = 0.10
ABS_IQ_BIN = 0.50

MIN_SCENARIOS_PER_REGION = 2

# A run of at least this many consecutive samples in the same
# candidate/scenario/observable region is considered a temporal segment.
MIN_RUN_LENGTH = 5


def finite(value: float) -> bool:
    return math.isfinite(value)


def quantize(value: float, width: float) -> int:
    return math.floor(value / width)


def mean(values: list[float]) -> float:
    if not values:
        return float("nan")
    return sum(values) / len(values)


def value_range(values: list[float]) -> float:
    if not values:
        return float("nan")
    return max(values) - min(values)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(
    path: Path,
    rows: list[dict],
    fieldnames: list[str],
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def region_key(row: dict) -> tuple[int, int, int]:
    return (
        quantize(float(row["error"]), ERROR_BIN),
        quantize(
            float(row["delta_error"]),
            DELTA_ERROR_BIN,
        ),
        quantize(float(row["abs_iq"]), ABS_IQ_BIN),
    )


def validate(rows: list[dict]) -> None:

    if len(rows) != 96_000:
        raise ValueError(
            f"Unexpected sample count: {len(rows)}"
        )

    fields = [
        "t",
        "omega_m",
        "error",
        "delta_error",
        "int_w",
        "iq_ref",
        "abs_iq",
        "iq",
        "te",
    ]

    for row in rows:
        for field in fields:
            value = float(row[field])
            if not finite(value):
                raise ValueError(
                    f"Non-finite {field}"
                )


def build_runs(rows: list[dict]) -> list[dict]:
    """
    Construct consecutive temporal runs inside each
    candidate/scenario trajectory.

    pre_profile is excluded.
    """

    ordered = sorted(
        rows,
        key=lambda row: (
            row["candidate"],
            row["scenario"],
            float(row["t"]),
        ),
    )

    runs = []

    current_key = None
    current_rows: list[dict] = []

    def flush() -> None:
        nonlocal current_rows

        if len(current_rows) >= MIN_RUN_LENGTH:
            first = current_rows[0]
            last = current_rows[-1]

            runs.append(
                {
                    "candidate": first["candidate"],
                    "scenario": first["scenario"],
                    "region": region_key(first),
                    "start_t": float(first["t"]),
                    "end_t": float(last["t"]),
                    "duration": (
                        float(last["t"])
                        - float(first["t"])
                    ),
                    "samples": len(current_rows),
                    "int_w_mean": mean(
                        [
                            float(row["int_w"])
                            for row in current_rows
                        ]
                    ),
                    "int_w_range": value_range(
                        [
                            float(row["int_w"])
                            for row in current_rows
                        ]
                    ),
                    "iq_ref_mean": mean(
                        [
                            float(row["iq_ref"])
                            for row in current_rows
                        ]
                    ),
                    "iq_ref_range": value_range(
                        [
                            float(row["iq_ref"])
                            for row in current_rows
                        ]
                    ),
                    "error_mean": mean(
                        [
                            float(row["error"])
                            for row in current_rows
                        ]
                    ),
                    "abs_iq_mean": mean(
                        [
                            float(row["abs_iq"])
                            for row in current_rows
                        ]
                    ),
                    "transition": first["transition"],
                }
            )

        current_rows = []

    for row in ordered:

        if row["transition"] == "pre_profile":
            continue

        key = (
            row["candidate"],
            row["scenario"],
            region_key(row),
        )

        if key != current_key:
            flush()
            current_key = key

        current_rows.append(row)

    flush()

    return runs


def main() -> None:

    print("=" * 72)
    print(" J2.3 — ANFIS TEMPORAL PERSISTENCE")
    print("=" * 72)

    if not INPUT_TRAJECTORIES.exists():
        raise FileNotFoundError(INPUT_TRAJECTORIES)

    if not INPUT_REGIONS.exists():
        raise FileNotFoundError(INPUT_REGIONS)

    rows = read_csv(INPUT_TRAJECTORIES)

    print(f"samples = {len(rows)}")

    validate(rows)

    print("dataset_validation = OK")

    # ------------------------------------------------------------------
    # Load only the J2.1 regions that passed its scenario criterion.
    # ------------------------------------------------------------------

    j21_regions = read_csv(INPUT_REGIONS)

    target_regions = {
        (
            row["candidate"],
            int(row["error_bin"]),
            int(row["delta_error_bin"]),
            int(row["abs_iq_bin"]),
        )
        for row in j21_regions
        if int(row["scenario_count"]) >= MIN_SCENARIOS_PER_REGION
    }

    print(
        "J2.1 target regions = "
        f"{len(target_regions)}"
    )

    # ------------------------------------------------------------------
    # Build temporal runs.
    # ------------------------------------------------------------------

    runs = build_runs(rows)

    print(
        "temporal runs >= "
        f"{MIN_RUN_LENGTH} samples = {len(runs)}"
    )

    # ------------------------------------------------------------------
    # Keep only runs belonging to J2.1 regions.
    # ------------------------------------------------------------------

    target_runs = []

    for run in runs:

        key = (
            run["candidate"],
            run["region"][0],
            run["region"][1],
            run["region"][2],
        )

        if key in target_regions:
            target_runs.append(run)

    print(
        "runs inside J2.1 regions = "
        f"{len(target_runs)}"
    )

    # ------------------------------------------------------------------
    # Aggregate by candidate + region + scenario.
    # ------------------------------------------------------------------

    grouped = defaultdict(list)

    for run in target_runs:

        key = (
            run["candidate"],
            run["region"],
            run["scenario"],
        )

        grouped[key].append(run)

    scenario_rows = []

    for (
        candidate,
        region,
        scenario,
    ), group in grouped.items():

        durations = [
            run["duration"]
            for run in group
        ]

        lengths = [
            run["samples"]
            for run in group
        ]

        int_means = [
            run["int_w_mean"]
            for run in group
        ]

        iq_means = [
            run["iq_ref_mean"]
            for run in group
        ]

        scenario_rows.append(
            {
                "candidate": candidate,
                "error_bin": region[0],
                "delta_error_bin": region[1],
                "abs_iq_bin": region[2],
                "scenario": scenario,
                "run_count": len(group),
                "total_samples": sum(lengths),
                "total_duration": sum(durations),
                "max_run_samples": max(lengths),
                "max_run_duration": max(durations),
                "mean_run_duration": mean(durations),
                "int_w_mean_range_across_runs":
                    value_range(int_means),
                "iq_ref_mean_range_across_runs":
                    value_range(iq_means),
            }
        )

    # ------------------------------------------------------------------
    # Region-level temporal overlap.
    # ------------------------------------------------------------------

    region_groups = defaultdict(list)

    for row in scenario_rows:

        region_groups[
            (
                row["candidate"],
                int(row["error_bin"]),
                int(row["delta_error_bin"]),
                int(row["abs_iq_bin"]),
            )
        ].append(row)

    region_rows = []

    for (
        candidate,
        error_bin,
        delta_error_bin,
        abs_iq_bin,
    ), group in region_groups.items():

        scenarios = sorted(
            row["scenario"]
            for row in group
        )

        total_duration = sum(
            float(row["total_duration"])
            for row in group
        )

        max_duration = max(
            float(row["max_run_duration"])
            for row in group
        )

        max_samples = max(
            int(row["max_run_samples"])
            for row in group
        )

        region_rows.append(
            {
                "candidate": candidate,
                "error_bin": error_bin,
                "delta_error_bin": delta_error_bin,
                "abs_iq_bin": abs_iq_bin,
                "scenario_count": len(scenarios),
                "scenario_list": ";".join(scenarios),
                "total_temporal_duration":
                    total_duration,
                "max_single_run_duration":
                    max_duration,
                "max_single_run_samples":
                    max_samples,
                "persistent": int(
                    max_duration > 0.001
                ),
            }
        )

    # ------------------------------------------------------------------
    # Scenario-to-scenario temporal comparison.
    #
    # We compare the aggregate temporal occupation of the same
    # candidate/region under different scenarios.
    # ------------------------------------------------------------------

    pair_rows = []

    for region_key_value, group in region_groups.items():

        if len(group) < MIN_SCENARIOS_PER_REGION:
            continue

        candidate, error_bin, delta_error_bin, abs_iq_bin = (
            region_key_value
        )

        by_scenario = {
            row["scenario"]: row
            for row in group
        }

        scenarios = sorted(by_scenario)

        for index, scenario_a in enumerate(scenarios):

            for scenario_b in scenarios[index + 1:]:

                a = by_scenario[scenario_a]
                b = by_scenario[scenario_b]

                pair_rows.append(
                    {
                        "candidate": candidate,
                        "error_bin": error_bin,
                        "delta_error_bin": delta_error_bin,
                        "abs_iq_bin": abs_iq_bin,
                        "scenario_a": scenario_a,
                        "scenario_b": scenario_b,
                        "duration_a":
                            a["total_duration"],
                        "duration_b":
                            b["total_duration"],
                        "max_run_duration_a":
                            a["max_run_duration"],
                        "max_run_duration_b":
                            b["max_run_duration"],
                        "max_run_samples_a":
                            a["max_run_samples"],
                        "max_run_samples_b":
                            b["max_run_samples"],
                        "duration_difference":
                            abs(
                                float(a["total_duration"])
                                - float(b["total_duration"])
                            ),
                        "max_run_duration_difference":
                            abs(
                                float(a["max_run_duration"])
                                - float(b["max_run_duration"])
                            ),
                        "int_w_mean_range_a":
                            a["int_w_mean_range_across_runs"],
                        "int_w_mean_range_b":
                            b["int_w_mean_range_across_runs"],
                        "iq_ref_mean_range_a":
                            a["iq_ref_mean_range_across_runs"],
                        "iq_ref_mean_range_b":
                            b["iq_ref_mean_range_across_runs"],
                    }
                )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write outputs.
    # ------------------------------------------------------------------

    # ``region`` is an internal tuple used during grouping.
    # It is intentionally not exported to the CSV.
    temporal_run_rows = []

    for run in target_runs:
        temporal_run_rows.append(
            {
                "candidate": run["candidate"],
                "scenario": run["scenario"],
                "error_bin": run["region"][0],
                "delta_error_bin": run["region"][1],
                "abs_iq_bin": run["region"][2],
                "start_t": run["start_t"],
                "end_t": run["end_t"],
                "duration": run["duration"],
                "samples": run["samples"],
                "int_w_mean": run["int_w_mean"],
                "int_w_range": run["int_w_range"],
                "iq_ref_mean": run["iq_ref_mean"],
                "iq_ref_range": run["iq_ref_range"],
                "error_mean": run["error_mean"],
                "abs_iq_mean": run["abs_iq_mean"],
                "transition": run["transition"],
            }
        )

    run_fields = [
        "candidate",
        "scenario",
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "start_t",
        "end_t",
        "duration",
        "samples",
        "int_w_mean",
        "int_w_range",
        "iq_ref_mean",
        "iq_ref_range",
        "error_mean",
        "abs_iq_mean",
        "transition",
    ]

    write_csv(
        OUTPUT_DIR / "j2_3_temporal_runs.csv",
        temporal_run_rows,
        run_fields,
    )

    scenario_fields = list(scenario_rows[0].keys()) if scenario_rows else []

    write_csv(
        OUTPUT_DIR / "j2_3_scenario_temporal_summary.csv",
        scenario_rows,
        scenario_fields,
    )

    region_fields = list(region_rows[0].keys()) if region_rows else []

    write_csv(
        OUTPUT_DIR / "j2_3_region_persistence.csv",
        region_rows,
        region_fields,
    )

    pair_fields = list(pair_rows[0].keys()) if pair_rows else []

    write_csv(
        OUTPUT_DIR / "j2_3_temporal_pairs.csv",
        pair_rows,
        pair_fields,
    )

    # ------------------------------------------------------------------
    # Console summary.
    # ------------------------------------------------------------------

    persistent_count = sum(
        row["persistent"]
        for row in region_rows
    )

    print()
    print("REGION PERSISTENCE")
    print("------------------")

    print(
        f"regions with temporal runs = "
        f"{len(region_rows)}"
    )

    print(
        f"regions with run > 1 ms = "
        f"{persistent_count}"
    )

    print()
    print("TOP REGIONS BY MAX TEMPORAL RUN")
    print("-------------------------------")

    top_regions = sorted(
        region_rows,
        key=lambda row:
        float(row["max_single_run_duration"]),
        reverse=True,
    )[:10]

    for row in top_regions:
        print(
            f"{row['candidate']} "
            f"samples={row['max_single_run_samples']:5d} "
            f"scenarios={row['scenario_list']} "
            f"max_run="
            f"{float(row['max_single_run_duration']):.6f} s "
            f"total="
            f"{float(row['total_temporal_duration']):.6f} s"
        )

    print()
    print("TOP TEMPORAL SCENARIO PAIRS")
    print("----------------------------")

    top_pairs = sorted(
        pair_rows,
        key=lambda row:
        float(row["max_run_duration_difference"]),
        reverse=True,
    )[:10]

    for row in top_pairs:
        print(
            f"{row['candidate']} "
            f"{row['scenario_a']} vs "
            f"{row['scenario_b']} "
            f"max_run="
            f"({float(row['max_run_duration_a']):.6f}, "
            f"{float(row['max_run_duration_b']):.6f}) s "
            f"Δduration="
            f"{float(row['max_run_duration_difference']):.6f} s"
        )

    print()
    print("OUTPUTS")
    print("-------")

    print(
        OUTPUT_DIR / "j2_3_temporal_runs.csv"
    )
    print(
        OUTPUT_DIR / "j2_3_scenario_temporal_summary.csv"
    )
    print(
        OUTPUT_DIR / "j2_3_region_persistence.csv"
    )
    print(
        OUTPUT_DIR / "j2_3_temporal_pairs.csv"
    )

    print()
    print("=" * 72)
    print(" J2.3 — ANÁLISIS COMPLETADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
