from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT_REGIONS = Path(
    "experiments/j2_1_anfis_intra_candidate/"
    "j2_1_observable_regions.csv"
)

INPUT_PAIRS = Path(
    "experiments/j2_1_anfis_intra_candidate/"
    "j2_1_scenario_pairs.csv"
)

OUTPUT_DIR = Path(
    "experiments/j2_2_anfis_region_characterization"
)


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


def f(row: dict, key: str) -> float:
    return float(row[key])


def scenario_dict(text: str) -> dict[str, float]:
    result = {}

    if not text:
        return result

    for item in text.split(";"):
        name, value = item.split(":", 1)
        result[name] = float(value)

    return result


def main() -> None:

    print("=" * 72)
    print(" J2.2 — ANFIS REGION CHARACTERIZATION")
    print("=" * 72)

    if not INPUT_REGIONS.exists():
        raise FileNotFoundError(INPUT_REGIONS)

    if not INPUT_PAIRS.exists():
        raise FileNotFoundError(INPUT_PAIRS)

    regions = read_csv(INPUT_REGIONS)
    pairs = read_csv(INPUT_PAIRS)

    print(f"regions input = {len(regions)}")
    print(f"scenario pairs input = {len(pairs)}")

    # Only regions that passed the J2.1 minimum criteria.
    regions = [
        row
        for row in regions
        if int(row["scenario_count"]) >= 2
    ]

    print(
        "regions retained after minimum scenario criterion = "
        f"{len(regions)}"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Distribution by candidate
    # ------------------------------------------------------------------

    candidate_counter = Counter(
        row["candidate"]
        for row in regions
    )

    candidate_rows = [
        {
            "candidate": candidate,
            "regions": candidate_counter[candidate],
        }
        for candidate in sorted(candidate_counter)
    ]

    write_csv(
        OUTPUT_DIR / "j2_2_candidate_distribution.csv",
        candidate_rows,
        ["candidate", "regions"],
    )

    # ------------------------------------------------------------------
    # 2. Distribution by scenario combination
    # ------------------------------------------------------------------

    scenario_counter = Counter(
        row["scenario_list"]
        for row in regions
    )

    scenario_rows = [
        {
            "scenario_combination": combination,
            "regions": count,
        }
        for combination, count in sorted(
            scenario_counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]

    write_csv(
        OUTPUT_DIR / "j2_2_scenario_distribution.csv",
        scenario_rows,
        ["scenario_combination", "regions"],
    )

    # ------------------------------------------------------------------
    # 3. Region-level characterization
    # ------------------------------------------------------------------

    region_rows = []

    for index, row in enumerate(regions, start=1):

        int_means = scenario_dict(
            row["scenario_int_w_means"]
        )

        iq_ref_means = scenario_dict(
            row["scenario_iq_ref_means"]
        )

        omega_means = scenario_dict(
            row["scenario_omega_means"]
        )

        te_means = scenario_dict(
            row["scenario_te_means"]
        )

        ordered_scenarios = [
            scenario
            for scenario in (
                "no_friction",
                "friction_base",
                "friction_medium",
                "friction_high",
            )
            if scenario in int_means
        ]

        int_values = [
            int_means[s]
            for s in ordered_scenarios
        ]

        iq_values = [
            iq_ref_means[s]
            for s in ordered_scenarios
        ]

        omega_values = [
            omega_means[s]
            for s in ordered_scenarios
        ]

        te_values = [
            te_means[s]
            for s in ordered_scenarios
        ]

        monotonic_int = False
        monotonic_iq = False
        monotonic_omega = False
        monotonic_te = False

        if len(ordered_scenarios) >= 3:

            int_diffs = [
                b - a
                for a, b in zip(int_values, int_values[1:])
            ]

            iq_diffs = [
                b - a
                for a, b in zip(iq_values, iq_values[1:])
            ]

            omega_diffs = [
                b - a
                for a, b in zip(
                    omega_values,
                    omega_values[1:],
                )
            ]

            te_diffs = [
                b - a
                for a, b in zip(
                    te_values,
                    te_values[1:],
                )
            ]

            monotonic_int = (
                all(d >= 0 for d in int_diffs)
                or all(d <= 0 for d in int_diffs)
            )

            monotonic_iq = (
                all(d >= 0 for d in iq_diffs)
                or all(d <= 0 for d in iq_diffs)
            )

            monotonic_omega = (
                all(d >= 0 for d in omega_diffs)
                or all(d <= 0 for d in omega_diffs)
            )

            monotonic_te = (
                all(d >= 0 for d in te_diffs)
                or all(d <= 0 for d in te_diffs)
            )

        region_rows.append(
            {
                "region_id": index,
                "candidate": row["candidate"],
                "error_bin": row["error_bin"],
                "delta_error_bin": row["delta_error_bin"],
                "abs_iq_bin": row["abs_iq_bin"],
                "samples_total": row["samples_total"],
                "scenario_count": row["scenario_count"],
                "scenario_list": row["scenario_list"],
                "int_w_mean_range": row[
                    "int_w_mean_range_between_scenarios"
                ],
                "iq_ref_mean_range": row[
                    "iq_ref_mean_range_between_scenarios"
                ],
                "omega_m_mean_range": row[
                    "omega_m_mean_range_between_scenarios"
                ],
                "te_mean_range": row[
                    "te_mean_range_between_scenarios"
                ],
                "int_w_monotonic": int(monotonic_int),
                "iq_ref_monotonic": int(monotonic_iq),
                "omega_m_monotonic": int(monotonic_omega),
                "te_monotonic": int(monotonic_te),
                "no_friction_int_w": int_means.get(
                    "no_friction", ""
                ),
                "friction_base_int_w": int_means.get(
                    "friction_base", ""
                ),
                "friction_medium_int_w": int_means.get(
                    "friction_medium", ""
                ),
                "friction_high_int_w": int_means.get(
                    "friction_high", ""
                ),
                "no_friction_iq_ref": iq_ref_means.get(
                    "no_friction", ""
                ),
                "friction_base_iq_ref": iq_ref_means.get(
                    "friction_base", ""
                ),
                "friction_medium_iq_ref": iq_ref_means.get(
                    "friction_medium", ""
                ),
                "friction_high_iq_ref": iq_ref_means.get(
                    "friction_high", ""
                ),
                "no_friction_omega_m": omega_means.get(
                    "no_friction", ""
                ),
                "friction_base_omega_m": omega_means.get(
                    "friction_base", ""
                ),
                "friction_medium_omega_m": omega_means.get(
                    "friction_medium", ""
                ),
                "friction_high_omega_m": omega_means.get(
                    "friction_high", ""
                ),
                "no_friction_te": te_means.get(
                    "no_friction", ""
                ),
                "friction_base_te": te_means.get(
                    "friction_base", ""
                ),
                "friction_medium_te": te_means.get(
                    "friction_medium", ""
                ),
                "friction_high_te": te_means.get(
                    "friction_high", ""
                ),
            }
        )

    region_fields = list(region_rows[0].keys()) if region_rows else []

    write_csv(
        OUTPUT_DIR / "j2_2_region_characterization.csv",
        region_rows,
        region_fields,
    )

    # ------------------------------------------------------------------
    # 4. Pairwise scenario characterization
    # ------------------------------------------------------------------

    pair_rows = []

    for row in pairs:

        int_difference = f(
            row,
            "abs_int_w_difference",
        )

        iq_difference = f(
            row,
            "abs_iq_ref_difference",
        )

        pair_rows.append(
            {
                "candidate": row["candidate"],
                "error_bin": row["error_bin"],
                "delta_error_bin": row["delta_error_bin"],
                "abs_iq_bin": row["abs_iq_bin"],
                "scenario_a": row["scenario_a"],
                "scenario_b": row["scenario_b"],
                "samples_a": row["samples_a"],
                "samples_b": row["samples_b"],
                "abs_int_w_difference":
                    row["abs_int_w_difference"],
                "abs_iq_ref_difference":
                    row["abs_iq_ref_difference"],
                "abs_omega_m_difference":
                    row["abs_omega_m_difference"],
                "abs_te_difference":
                    row["abs_te_difference"],
                "int_w_difference_flag": int(
                    int_difference >= 0.01
                ),
                "iq_ref_difference_flag": int(
                    iq_difference >= 0.50
                ),
            }
        )

    pair_fields = list(pair_rows[0].keys()) if pair_rows else []

    write_csv(
        OUTPUT_DIR / "j2_2_pair_characterization.csv",
        pair_rows,
        pair_fields,
    )

    # ------------------------------------------------------------------
    # 5. Aggregate statistics
    # ------------------------------------------------------------------

    total_regions = len(region_rows)

    monotonic_int_count = sum(
        row["int_w_monotonic"]
        for row in region_rows
    )

    monotonic_iq_count = sum(
        row["iq_ref_monotonic"]
        for row in region_rows
    )

    monotonic_omega_count = sum(
        row["omega_m_monotonic"]
        for row in region_rows
    )

    monotonic_te_count = sum(
        row["te_monotonic"]
        for row in region_rows
    )

    aggregate_rows = [
        {
            "metric": "regions",
            "value": total_regions,
        },
        {
            "metric": "regions_int_w_monotonic",
            "value": monotonic_int_count,
        },
        {
            "metric": "regions_iq_ref_monotonic",
            "value": monotonic_iq_count,
        },
        {
            "metric": "regions_omega_m_monotonic",
            "value": monotonic_omega_count,
        },
        {
            "metric": "regions_te_monotonic",
            "value": monotonic_te_count,
        },
        {
            "metric": "scenario_pairs",
            "value": len(pair_rows),
        },
        {
            "metric": "scenario_pairs_int_w_flagged",
            "value": sum(
                row["int_w_difference_flag"]
                for row in pair_rows
            ),
        },
        {
            "metric": "scenario_pairs_iq_ref_flagged",
            "value": sum(
                row["iq_ref_difference_flag"]
                for row in pair_rows
            ),
        },
    ]

    write_csv(
        OUTPUT_DIR / "j2_2_aggregate_summary.csv",
        aggregate_rows,
        ["metric", "value"],
    )

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------

    print()
    print("CANDIDATE DISTRIBUTION")
    print("----------------------")

    for row in candidate_rows:
        print(
            f"{row['candidate']}: "
            f"{row['regions']} regions"
        )

    print()
    print("SCENARIO COMBINATIONS")
    print("---------------------")

    for row in scenario_rows:
        print(
            f"{row['regions']:3d} regions: "
            f"{row['scenario_combination']}"
        )

    print()
    print("MONOTONICITY CHECK")
    print("-------------------")

    print(
        f"int_w      = "
        f"{monotonic_int_count}/{total_regions}"
    )

    print(
        f"iq_ref     = "
        f"{monotonic_iq_count}/{total_regions}"
    )

    print(
        f"omega_m    = "
        f"{monotonic_omega_count}/{total_regions}"
    )

    print(
        f"te         = "
        f"{monotonic_te_count}/{total_regions}"
    )

    print()
    print("TOP REGIONS BY int_w SCENARIO RANGE")
    print("------------------------------------")

    top_regions = sorted(
        region_rows,
        key=lambda row:
        float(row["int_w_mean_range"]),
        reverse=True,
    )[:10]

    for row in top_regions:
        print(
            f"R{row['region_id']:02d} "
            f"candidate={row['candidate']} "
            f"samples={row['samples_total']} "
            f"scenarios={row['scenario_list']} "
            f"Δint_w={float(row['int_w_mean_range']):.9f} "
            f"Δiq_ref={float(row['iq_ref_mean_range']):.9f} "
            f"monotonic_int={row['int_w_monotonic']}"
        )

    print()
    print("OUTPUTS")
    print("-------")

    print(
        OUTPUT_DIR / "j2_2_candidate_distribution.csv"
    )
    print(
        OUTPUT_DIR / "j2_2_scenario_distribution.csv"
    )
    print(
        OUTPUT_DIR / "j2_2_region_characterization.csv"
    )
    print(
        OUTPUT_DIR / "j2_2_pair_characterization.csv"
    )
    print(
        OUTPUT_DIR / "j2_2_aggregate_summary.csv"
    )

    print()
    print("=" * 72)
    print(" J2.2 — ANÁLISIS COMPLETADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
