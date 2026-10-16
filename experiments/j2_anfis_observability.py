from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


INPUT_FILE = Path(
    "experiments/j1_anfis_analysis/j1_temporal_trajectories.csv"
)

OUTPUT_DIR = Path("experiments/j2_anfis_observability")

# ---------------------------------------------------------------------------
# J2 diagnostic configuration
# ---------------------------------------------------------------------------

# Quantization widths for the proposed ANFIS observable state:
#
#   z = [error, delta_error, abs_iq]
#
# These are diagnostic bins, not physical equivalence classes.
ERROR_BIN = 0.10
DELTA_ERROR_BIN = 0.10
ABS_IQ_BIN = 0.50

MIN_SAMPLES_PER_REGION = 20
MIN_CANDIDATES_PER_REGION = 2
MIN_SCENARIOS_PER_REGION = 2

# A region is considered diagnostically interesting when the hidden/internal
# state varies enough despite similar observable inputs.
MIN_INT_W_RANGE = 0.01
MIN_IQ_REF_RANGE = 0.50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def finite(value: float) -> bool:
    return math.isfinite(value)


def quantize(value: float, width: float) -> int:
    return math.floor(value / width)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []

        for raw in reader:
            row = {
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
            rows.append(row)

    return rows


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


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------

def validate_dataset(rows: list[dict]) -> None:
    required_numeric = [
        "t",
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
        for field in required_numeric:
            if not finite(row[field]):
                raise ValueError(
                    f"Non-finite value in field {field}"
                )

    expected_samples = 96_000

    if len(rows) != expected_samples:
        raise ValueError(
            f"Unexpected number of samples: "
            f"{len(rows)} != {expected_samples}"
        )


# ---------------------------------------------------------------------------
# Observable-region construction
# ---------------------------------------------------------------------------

def build_regions(rows: list[dict]) -> dict:
    regions: dict[tuple[int, int, int], list[dict]] = defaultdict(list)

    for row in rows:
        # The initial pre_profile state is excluded from the observability
        # analysis because it is not a reference-transition segment.
        if row["transition"] == "pre_profile":
            continue

        key = (
            quantize(row["error"], ERROR_BIN),
            quantize(row["delta_error"], DELTA_ERROR_BIN),
            quantize(row["abs_iq"], ABS_IQ_BIN),
        )

        regions[key].append(row)

    return regions


# ---------------------------------------------------------------------------
# Region diagnostics
# ---------------------------------------------------------------------------

def analyze_regions(
    regions: dict[tuple[int, int, int], list[dict]]
) -> list[dict]:

    output = []

    for key, subset in regions.items():
        if len(subset) < MIN_SAMPLES_PER_REGION:
            continue

        candidates = sorted(
            {row["candidate"] for row in subset}
        )

        scenarios = sorted(
            {row["scenario"] for row in subset}
        )

        transitions = sorted(
            {row["transition"] for row in subset}
        )

        if len(candidates) < MIN_CANDIDATES_PER_REGION:
            continue

        if len(scenarios) < MIN_SCENARIOS_PER_REGION:
            continue

        int_w = [row["int_w"] for row in subset]
        iq_ref = [row["iq_ref"] for row in subset]
        kp = [row["kp"] for row in subset]
        ki = [row["ki"] for row in subset]

        error = [row["error"] for row in subset]
        delta_error = [row["delta_error"] for row in subset]
        abs_iq = [row["abs_iq"] for row in subset]

        int_range = value_range(int_w)
        iq_ref_range = value_range(iq_ref)
        kp_range = value_range(kp)
        ki_range = value_range(ki)

        interesting = (
            int_range >= MIN_INT_W_RANGE
            or iq_ref_range >= MIN_IQ_REF_RANGE
        )

        output.append(
            {
                "error_bin": key[0],
                "delta_error_bin": key[1],
                "abs_iq_bin": key[2],
                "samples": len(subset),
                "candidates": len(candidates),
                "candidate_list": ";".join(candidates),
                "scenarios": len(scenarios),
                "scenario_list": ";".join(scenarios),
                "transitions": len(transitions),
                "transition_list": ";".join(transitions),
                "error_mean": mean(error),
                "delta_error_mean": mean(delta_error),
                "abs_iq_mean": mean(abs_iq),
                "int_w_mean": mean(int_w),
                "int_w_range": int_range,
                "int_w_p95": percentile(int_w, 95),
                "iq_ref_mean": mean(iq_ref),
                "iq_ref_range": iq_ref_range,
                "kp_range": kp_range,
                "ki_range": ki_range,
                "interesting": int(interesting),
            }
        )

    return output


# ---------------------------------------------------------------------------
# Candidate/scenario contrast inside observable regions
# ---------------------------------------------------------------------------

def analyze_contrasts(
    regions: dict[tuple[int, int, int], list[dict]]
) -> list[dict]:

    output = []

    for key, subset in regions.items():
        if len(subset) < MIN_SAMPLES_PER_REGION:
            continue

        candidates = sorted(
            {row["candidate"] for row in subset}
        )

        scenarios = sorted(
            {row["scenario"] for row in subset}
        )

        if len(candidates) < MIN_CANDIDATES_PER_REGION:
            continue

        if len(scenarios) < MIN_SCENARIOS_PER_REGION:
            continue

        grouped = defaultdict(list)

        for row in subset:
            grouped[
                (
                    row["candidate"],
                    row["scenario"],
                )
            ].append(row)

        for group_key, group in grouped.items():
            int_w = [row["int_w"] for row in group]
            iq_ref = [row["iq_ref"] for row in group]

            output.append(
                {
                    "error_bin": key[0],
                    "delta_error_bin": key[1],
                    "abs_iq_bin": key[2],
                    "candidate": group_key[0],
                    "scenario": group_key[1],
                    "samples": len(group),
                    "int_w_mean": mean(int_w),
                    "int_w_range": value_range(int_w),
                    "iq_ref_mean": mean(iq_ref),
                    "iq_ref_range": value_range(iq_ref),
                }
            )

    return output


# ---------------------------------------------------------------------------
# Pairwise observable-state comparison
# ---------------------------------------------------------------------------

def analyze_candidate_pairs(
    rows: list[dict],
) -> list[dict]:

    grouped = defaultdict(list)

    for row in rows:
        if row["transition"] == "pre_profile":
            continue

        key = (
            quantize(row["error"], ERROR_BIN),
            quantize(row["delta_error"], DELTA_ERROR_BIN),
            quantize(row["abs_iq"], ABS_IQ_BIN),
        )

        grouped[key].append(row)

    output = []

    for key, subset in grouped.items():
        candidate_rows = defaultdict(list)

        for row in subset:
            candidate_rows[row["candidate"]].append(row)

        candidates = sorted(candidate_rows)

        if len(candidates) < MIN_CANDIDATES_PER_REGION:
            continue

        for index, candidate_a in enumerate(candidates):
            for candidate_b in candidates[index + 1:]:
                a = candidate_rows[candidate_a]
                b = candidate_rows[candidate_b]

                int_a = mean([row["int_w"] for row in a])
                int_b = mean([row["int_w"] for row in b])

                iqref_a = mean([row["iq_ref"] for row in a])
                iqref_b = mean([row["iq_ref"] for row in b])

                output.append(
                    {
                        "error_bin": key[0],
                        "delta_error_bin": key[1],
                        "abs_iq_bin": key[2],
                        "candidate_a": candidate_a,
                        "candidate_b": candidate_b,
                        "samples_a": len(a),
                        "samples_b": len(b),
                        "int_w_mean_a": int_a,
                        "int_w_mean_b": int_b,
                        "abs_int_w_difference": abs(int_a - int_b),
                        "iq_ref_mean_a": iqref_a,
                        "iq_ref_mean_b": iqref_b,
                        "abs_iq_ref_difference": abs(
                            iqref_a - iqref_b
                        ),
                    }
                )

    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print(" J2 — ANFIS OBSERVABILITY DIAGNOSTIC")
    print("=" * 72)

    print(f"input = {INPUT_FILE}")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"J1 trajectory file not found: {INPUT_FILE}"
        )

    rows = read_csv(INPUT_FILE)

    print(f"samples = {len(rows)}")

    validate_dataset(rows)

    print("dataset_validation = OK")

    print()
    print("PROPOSED OBSERVABLE STATE")
    print("--------------------------")
    print("z = [error, delta_error, abs_iq]")

    print()
    print("DIAGNOSTIC BIN WIDTHS")
    print("----------------------")
    print(f"error      = {ERROR_BIN}")
    print(f"delta_error= {DELTA_ERROR_BIN}")
    print(f"abs_iq     = {ABS_IQ_BIN}")

    regions = build_regions(rows)

    print()
    print("REGIONS")
    print("-------")
    print(f"total quantized regions = {len(regions)}")

    region_rows = analyze_regions(regions)

    interesting_rows = [
        row
        for row in region_rows
        if row["interesting"] == 1
    ]

    print(
        "regions passing minimum diversity criteria = "
        f"{len(region_rows)}"
    )

    print(
        "regions with internal-state/action variation = "
        f"{len(interesting_rows)}"
    )

    contrast_rows = analyze_contrasts(regions)

    pair_rows = analyze_candidate_pairs(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    region_fields = [
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "samples",
        "candidates",
        "candidate_list",
        "scenarios",
        "scenario_list",
        "transitions",
        "transition_list",
        "error_mean",
        "delta_error_mean",
        "abs_iq_mean",
        "int_w_mean",
        "int_w_range",
        "int_w_p95",
        "iq_ref_mean",
        "iq_ref_range",
        "kp_range",
        "ki_range",
        "interesting",
    ]

    contrast_fields = [
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "candidate",
        "scenario",
        "samples",
        "int_w_mean",
        "int_w_range",
        "iq_ref_mean",
        "iq_ref_range",
    ]

    pair_fields = [
        "error_bin",
        "delta_error_bin",
        "abs_iq_bin",
        "candidate_a",
        "candidate_b",
        "samples_a",
        "samples_b",
        "int_w_mean_a",
        "int_w_mean_b",
        "abs_int_w_difference",
        "iq_ref_mean_a",
        "iq_ref_mean_b",
        "abs_iq_ref_difference",
    ]

    write_csv(
        OUTPUT_DIR / "j2_observable_regions.csv",
        region_rows,
        region_fields,
    )

    write_csv(
        OUTPUT_DIR / "j2_region_contrasts.csv",
        contrast_rows,
        contrast_fields,
    )

    write_csv(
        OUTPUT_DIR / "j2_candidate_pairs.csv",
        pair_rows,
        pair_fields,
    )

    # -----------------------------------------------------------------------
    # Console diagnostics
    # -----------------------------------------------------------------------

    print()
    print("TOP REGIONS BY int_w RANGE")
    print("--------------------------")

    top_regions = sorted(
        interesting_rows,
        key=lambda row: (
            row["int_w_range"],
            row["iq_ref_range"],
            row["samples"],
        ),
        reverse=True,
    )[:10]

    for row in top_regions:
        print(
            f"samples={row['samples']:5d} "
            f"candidates={row['candidate_list']} "
            f"scenarios={row['scenario_list']} "
            f"int_w_range={row['int_w_range']:.8f} "
            f"iq_ref_range={row['iq_ref_range']:.8f}"
        )

    print()
    print("TOP CANDIDATE PAIRS BY |iq_ref| DIFFERENCE")
    print("--------------------------------------------")

    top_pairs = sorted(
        pair_rows,
        key=lambda row: row["abs_iq_ref_difference"],
        reverse=True,
    )[:10]

    for row in top_pairs:
        print(
            f"{row['candidate_a']} vs {row['candidate_b']} "
            f"samples=({row['samples_a']},{row['samples_b']}) "
            f"|Δiq_ref|={row['abs_iq_ref_difference']:.8f} "
            f"|Δint_w|={row['abs_int_w_difference']:.8f}"
        )

    print()
    print("OUTPUTS")
    print("-------")
    print(
        OUTPUT_DIR / "j2_observable_regions.csv"
    )
    print(
        OUTPUT_DIR / "j2_region_contrasts.csv"
    )
    print(
        OUTPUT_DIR / "j2_candidate_pairs.csv"
    )

    print()
    print("=" * 72)
    print(" J2 — ANÁLISIS COMPLETADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
