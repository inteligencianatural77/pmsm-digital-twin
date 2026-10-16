from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


INPUT_FILE = Path(
    "experiments/j1_anfis_analysis/j1_temporal_trajectories.csv"
)

OUTPUT_DIR = Path("experiments/j2_1_anfis_intra_candidate")

# ---------------------------------------------------------------------------
# Diagnostic configuration
# ---------------------------------------------------------------------------

# Same observable state proposed for ANFIS:
#
#     z = [error, delta_error, abs_iq]
#
# These are diagnostic quantization widths.
# They do NOT define physical equivalence classes.

ERROR_BIN = 0.10
DELTA_ERROR_BIN = 0.10
ABS_IQ_BIN = 0.50

MIN_SAMPLES_PER_SCENARIO = 20
MIN_SCENARIOS_PER_REGION = 2

# Minimum differences used only to flag potentially interesting regions.
# They are diagnostic thresholds, NOT performance criteria.
MIN_INT_W_DIFFERENCE = 0.01
MIN_IQ_REF_DIFFERENCE = 0.50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * p / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower]
        + fraction * (ordered[upper] - ordered[lower])
    )


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)

        rows = []

        for raw in reader:
            rows.append(
                {
                    "t": float(raw["t"]),
                    "candidate": raw["candidate"],
                    "scenario": raw["scenario"],
                    "kp_factor": float(raw["kp_factor"]),
                    "ki_factor": float(raw["ki_factor"]),
                    "kp": float(raw["kp"]),
                    "ki": float(raw["ki"]),
                    "transition": raw["transition"],
                    "omega_ref": float(raw["omega_ref"]),
                    "omega_m": float(raw["omega_m"]),
                    "error": float(raw["error"]),
                    "delta_error": float(raw["delta_error"]),
                    "int_w": float(raw["int_w"]),
                    "iq_ref": float(raw["iq_ref"]),
                    "abs_iq": float(raw["abs_iq"]),
                    "iq": float(raw["iq"]),
                    "id": float(raw["id"]),
                    "te": float(raw["te"]),
                    "tf": float(raw["tf"]),
                }
            )

    return rows


def write_csv(
    path: Path,
    rows: list[dict],
    fieldnames: list[str],
) -> None:

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_dataset(rows: list[dict]) -> None:

    if len(rows) != 96_000:
        raise ValueError(
            f"Unexpected sample count: {len(rows)}"
        )

    numeric_fields = [
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
    ]

    for row in rows:
        for field in numeric_fields:
            if not finite(row[field]):
                raise ValueError(
                    f"Non-finite value in field: {field}"
                )


# ---------------------------------------------------------------------------
# Region construction
# ---------------------------------------------------------------------------

def region_key(row: dict) -> tuple[int, int, int]:

    return (
        quantize(row["error"], ERROR_BIN),
        quantize(row["delta_error"], DELTA_ERROR_BIN),
        quantize(row["abs_iq"], ABS_IQ_BIN),
    )


def build_groups(rows: list[dict]) -> dict:

    groups = defaultdict(list)

    for row in rows:

        # pre_profile is not a reference transition and is excluded.
        if row["transition"] == "pre_profile":
            continue

        key = (
            row["candidate"],
            region_key(row),
        )

        groups[key].append(row)

    return groups


# ---------------------------------------------------------------------------
# Intra-candidate / inter-scenario analysis
# ---------------------------------------------------------------------------

def analyze_groups(groups: dict) -> list[dict]:

    output = []

    for (candidate, region), subset in groups.items():

        scenario_groups = defaultdict(list)

        for row in subset:
            scenario_groups[row["scenario"]].append(row)

        valid_scenarios = {
            scenario: rows
            for scenario, rows in scenario_groups.items()
            if len(rows) >= MIN_SAMPLES_PER_SCENARIO
        }

        if len(valid_scenarios) < MIN_SCENARIOS_PER_REGION:
            continue

        int_means = {
            scenario: mean(
                [row["int_w"] for row in scenario_rows]
            )
            for scenario, scenario_rows in valid_scenarios.items()
        }

        iq_ref_means = {
            scenario: mean(
                [row["iq_ref"] for row in scenario_rows]
            )
            for scenario, scenario_rows in valid_scenarios.items()
        }

        omega_means = {
            scenario: mean(
                [row["omega_m"] for row in scenario_rows]
            )
            for scenario, scenario_rows in valid_scenarios.items()
        }

        te_means = {
            scenario: mean(
                [row["te"] for row in scenario_rows]
            )
            for scenario, scenario_rows in valid_scenarios.items()
        }

        int_values = [
            value
            for scenario_rows in valid_scenarios.values()
            for value in [row["int_w"] for row in scenario_rows]
        ]

        iq_ref_values = [
            value
            for scenario_rows in valid_scenarios.values()
            for value in [row["iq_ref"] for row in scenario_rows]
        ]

        int_mean_values = list(int_means.values())
        iq_ref_mean_values = list(iq_ref_means.values())

        int_mean_range = value_range(int_mean_values)
        iq_ref_mean_range = value_range(iq_ref_mean_values)

        interesting = (
            int_mean_range >= MIN_INT_W_DIFFERENCE
            or iq_ref_mean_range >= MIN_IQ_REF_DIFFERENCE
        )

        output.append(
            {
                "candidate": candidate,
                "error_bin": region[0],
                "delta_error_bin": region[1],
                "abs_iq_bin": region[2],
                "samples_total": sum(
                    len(rows)
                    for rows in valid_scenarios.values()
                ),
                "scenario_count": len(valid_scenarios),
                "scenario_list": ";".join(
                    sorted(valid_scenarios)
                ),
                "int_w_global_range": value_range(int_values),
                "iq_ref_global_range": value_range(
                    iq_ref_values
                ),
                "int_w_mean_range_between_scenarios":
                    int_mean_range,
                "iq_ref_mean_range_between_scenarios":
                    iq_ref_mean_range,
                "omega_m_mean_range_between_scenarios":
                    value_range(list(omega_means.values())),
                "te_mean_range_between_scenarios":
                    value_range(list(te_means.values())),
                "interesting": int(interesting),
                "scenario_int_w_means":
                    ";".join(
                        f"{scenario}:{int_means[scenario]:.9f}"
                        for scenario in sorted(int_means)
                    ),
                "scenario_iq_ref_means":
                    ";".join(
                        f"{scenario}:{iq_ref_means[scenario]:.9f}"
                        for scenario in sorted(iq_ref_means)
                    ),
                "scenario_omega_means":
                    ";".join(
                        f"{scenario}:{omega_means[scenario]:.9f}"
                        for scenario in sorted(omega_means)
                    ),
                "scenario_te_means":
                    ";".join(
                        f"{scenario}:{te_means[scenario]:.9f}"
                        for scenario in sorted(te_means)
                    ),
            }
        )

    return output


# ---------------------------------------------------------------------------
# Pairwise scenario comparison
# ---------------------------------------------------------------------------

def analyze_scenario_pairs(
    groups: dict,
) -> list[dict]:

    output = []

    for (candidate, region), subset in groups.items():

        scenario_groups = defaultdict(list)

        for row in subset:
            scenario_groups[row["scenario"]].append(row)

        valid = {
            scenario: scenario_rows
            for scenario, scenario_rows in scenario_groups.items()
            if len(scenario_rows) >= MIN_SAMPLES_PER_SCENARIO
        }

        scenarios = sorted(valid)

        if len(scenarios) < MIN_SCENARIOS_PER_REGION:
            continue

        for index, scenario_a in enumerate(scenarios):

            for scenario_b in scenarios[index + 1:]:

                a = valid[scenario_a]
                b = valid[scenario_b]

                int_a = mean([row["int_w"] for row in a])
                int_b = mean([row["int_w"] for row in b])

                iq_a = mean([row["iq_ref"] for row in a])
                iq_b = mean([row["iq_ref"] for row in b])

                omega_a = mean([row["omega_m"] for row in a])
                omega_b = mean([row["omega_m"] for row in b])

                te_a = mean([row["te"] for row in a])
                te_b = mean([row["te"] for row in b])

                output.append(
                    {
                        "candidate": candidate,
                        "error_bin": region[0],
                        "delta_error_bin": region[1],
                        "abs_iq_bin": region[2],
                        "scenario_a": scenario_a,
                        "scenario_b": scenario_b,
                        "samples_a": len(a),
                        "samples_b": len(b),
                        "int_w_mean_a": int_a,
                        "int_w_mean_b": int_b,
                        "abs_int_w_difference":
                            abs(int_a - int_b),
                        "iq_ref_mean_a": iq_a,
                        "iq_ref_mean_b": iq_b,
                        "abs_iq_ref_difference":
                            abs(iq_a - iq_b),
                        "omega_m_mean_a": omega_a,
                        "omega_m_mean_b": omega_b,
                        "abs_omega_m_difference":
                            abs(omega_a - omega_b),
                        "te_mean_a": te_a,
                        "te_mean_b": te_b,
                        "abs_te_difference":
                            abs(te_a - te_b),
                    }
                )

    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    print("=" * 72)
    print(" J2.1 — INTRA-CANDIDATE / INTER-SCENARIO DIAGNOSTIC")
    print("=" * 72)

    print(f"input = {INPUT_FILE}")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    rows = read_csv(INPUT_FILE)

    print(f"samples = {len(rows)}")

    validate_dataset(rows)

    print("dataset_validation = OK")

    print()
    print("OBSERVABLE STATE")
    print("----------------")
    print("z = [error, delta_error, abs_iq]")

    print()
    print("BIN WIDTHS")
    print("----------")
    print(f"error       = {ERROR_BIN}")
    print(f"delta_error = {DELTA_ERROR_BIN}")
    print(f"abs_iq      = {ABS_IQ_BIN}")

    groups = build_groups(rows)

    print()
    print("GROUPS")
    print("------")
    print(
        f"candidate × observable regions = {len(groups)}"
    )

    region_rows = analyze_groups(groups)

    interesting_rows = [
        row
        for row in region_rows
        if row["interesting"] == 1
    ]

    print(
        "regions with >= 2 valid scenarios = "
        f"{len(region_rows)}"
    )

    print(
        "regions flagged for scenario-dependent "
        f"variation = {len(interesting_rows)}"
    )

    pair_rows = analyze_scenario_pairs(groups)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    region_fields = [
        "candidate",
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "samples_total",
        "scenario_count",
        "scenario_list",
        "int_w_global_range",
        "iq_ref_global_range",
        "int_w_mean_range_between_scenarios",
        "iq_ref_mean_range_between_scenarios",
        "omega_m_mean_range_between_scenarios",
        "te_mean_range_between_scenarios",
        "interesting",
        "scenario_int_w_means",
        "scenario_iq_ref_means",
        "scenario_omega_means",
        "scenario_te_means",
    ]

    pair_fields = [
        "candidate",
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "scenario_a",
        "scenario_b",
        "samples_a",
        "samples_b",
        "int_w_mean_a",
        "int_w_mean_b",
        "abs_int_w_difference",
        "iq_ref_mean_a",
        "iq_ref_mean_b",
        "abs_iq_ref_difference",
        "omega_m_mean_a",
        "omega_m_mean_b",
        "abs_omega_m_difference",
        "te_mean_a",
        "te_mean_b",
        "abs_te_difference",
    ]

    write_csv(
        OUTPUT_DIR / "j2_1_observable_regions.csv",
        region_rows,
        region_fields,
    )

    write_csv(
        OUTPUT_DIR / "j2_1_scenario_pairs.csv",
        pair_rows,
        pair_fields,
    )

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------

    print()
    print("TOP REGIONS BY BETWEEN-SCENARIO int_w DIFFERENCE")
    print("-----------------------------------------------")

    top_int = sorted(
        region_rows,
        key=lambda row:
        row["int_w_mean_range_between_scenarios"],
        reverse=True,
    )[:10]

    for row in top_int:
        print(
            f"{row['candidate']} "
            f"samples={row['samples_total']:5d} "
            f"scenarios={row['scenario_list']} "
            f"Δint_w="
            f"{row['int_w_mean_range_between_scenarios']:.9f} "
            f"Δiq_ref="
            f"{row['iq_ref_mean_range_between_scenarios']:.9f}"
        )

    print()
    print("TOP SCENARIO PAIRS BY |Δint_w|")
    print("-------------------------------")

    top_pairs = sorted(
        pair_rows,
        key=lambda row: row["abs_int_w_difference"],
        reverse=True,
    )[:10]

    for row in top_pairs:
        print(
            f"{row['candidate']} "
            f"{row['scenario_a']} vs "
            f"{row['scenario_b']} "
            f"samples=({row['samples_a']},"
            f"{row['samples_b']}) "
            f"|Δint_w|="
            f"{row['abs_int_w_difference']:.9f} "
            f"|Δiq_ref|="
            f"{row['abs_iq_ref_difference']:.9f}"
        )

    print()
    print("OUTPUTS")
    print("-------")
    print(
        OUTPUT_DIR / "j2_1_observable_regions.csv"
    )
    print(
        OUTPUT_DIR / "j2_1_scenario_pairs.csv"
    )

    print()
    print("=" * 72)
    print(" J2.1 — ANÁLISIS COMPLETADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
