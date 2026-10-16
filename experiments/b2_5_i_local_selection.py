import csv
from collections import defaultdict
from pathlib import Path

METRICS = Path("experiments/b2_5_parameter_sweep_metrics.csv")
OUT_DIR = Path("experiments/b2_5_analysis")

I_MAX = 79.5

# ------------------------------------------------------------
# Lectura
# ------------------------------------------------------------

with METRICS.open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

# ------------------------------------------------------------
# Agrupar por condición local + configuración
# ------------------------------------------------------------

groups = defaultdict(list)

for r in rows:
    key = (
        r["scenario"],
        r["transition"],
        float(r["kp_factor"]),
        float(r["ki_factor"]),
    )
    groups[key].append(r)

# ------------------------------------------------------------
# Construir configuraciones locales admisibles
# ------------------------------------------------------------

local_configs = defaultdict(list)

for key, group in groups.items():

    if len(group) != 1:
        raise RuntimeError(
            f"Configuración local inesperada: {key} "
            f"-> {len(group)} filas"
        )

    r = group[0]

    scenario, transition, kp_f, ki_f = key

    iq_max = float(r["iq_ref_max_A"])

    # Restricción física/documental local.
    if iq_max > I_MAX:
        continue

    local_configs[(scenario, transition)].append({
        "scenario": scenario,
        "transition": transition,
        "kp_f": kp_f,
        "ki_f": ki_f,
        "mae": float(r["mae_rad_s"]),
        "rmse": float(r["rmse_rad_s"]),
        "final_error": float(r["final_abs_error_rad_s"]),
        "iq_max": iq_max,
        "margin": I_MAX - iq_max,
        "te_max": float(r["te_max_Nm"]),
    })

if len(local_configs) != 16:
    raise RuntimeError(
        f"Se esperaban 16 condiciones locales; "
        f"se encontraron {len(local_configs)}."
    )

# ------------------------------------------------------------
# Normalización local
# ------------------------------------------------------------



# ------------------------------------------------------------
# Barrido multicriterio local
def normalize(values):
    lo = min(values.values())
    hi = max(values.values())

    if hi == lo:
        return {k: 0.0 for k in values}

    return {
        k: (v - lo) / (hi - lo)
        for k, v in values.items()
    }
# ------------------------------------------------------------

results = []

for condition in sorted(local_configs):

    points = local_configs[condition]

    if len(points) != 14:
        raise RuntimeError(
            f"{condition}: se esperaban 14 configuraciones "
            f"admisibles; se encontraron {len(points)}."
        )

    mae_values = {
        i: p["mae"]
        for i, p in enumerate(points)
    }

    iq_values = {
        i: p["iq_max"]
        for i, p in enumerate(points)
    }

    mae_norm = normalize(mae_values)
    iq_norm = normalize(iq_values)

    for i, p in enumerate(points):
        p["mae_norm"] = mae_norm[i]
        p["iq_norm"] = iq_norm[i]

    for alpha_index in range(21):

        alpha = alpha_index / 20.0

        scored = []

        for p in points:

            score = (
                alpha * p["mae_norm"]
                +
                (1.0 - alpha) * p["iq_norm"]
            )

            scored.append((score, p))

        best_score = min(x[0] for x in scored)

        winners = [
            (score, p)
            for score, p in scored
            if abs(score - best_score) < 1e-12
        ]

        for score, p in winners:

            results.append({
                "scenario": condition[0],
                "transition": condition[1],
                "alpha_error": alpha,
                "kp_factor": p["kp_f"],
                "ki_factor": p["ki_f"],
                "score": score,
                "mae": p["mae"],
                "rmse": p["rmse"],
                "final_error": p["final_error"],
                "iq_max": p["iq_max"],
                "current_margin": p["margin"],
                "te_max": p["te_max"],
            })

# ------------------------------------------------------------
# Mostrar resultados completos
# ------------------------------------------------------------

print("=" * 115)
print("B2.5-I — SELECCIÓN MULTICRITERIO LOCAL")
print("=" * 115)

current_condition = None

for r in results:

    condition = (
        r["scenario"],
        r["transition"],
    )

    if condition != current_condition:

        current_condition = condition

        print()
        print("-" * 115)
        print(
            f"ESCENARIO: {condition[0]}"
        )
        print(
            f"TRANSICIÓN: {condition[1]}"
        )
        print("-" * 115)

        print(
            f"{'alpha':>7} "
            f"{'Kp_f':>6} "
            f"{'Ki_f':>6} "
            f"{'Score':>10} "
            f"{'MAE':>10} "
            f"{'Iqmax':>10} "
            f"{'Margen':>10}"
        )

    print(
        f"{r['alpha_error']:7.2f} "
        f"{r['kp_factor']:6.2f} "
        f"{r['ki_factor']:6.2f} "
        f"{r['score']:10.6f} "
        f"{r['mae']:10.6f} "
        f"{r['iq_max']:10.6f} "
        f"{r['current_margin']:10.6f}"
    )

# ------------------------------------------------------------
# Consolidar intervalos de alpha
# ------------------------------------------------------------

intervals = defaultdict(list)

for r in results:

    key = (
        r["scenario"],
        r["transition"],
        r["kp_factor"],
        r["ki_factor"],
    )

    intervals[key].append(r["alpha_error"])

print()
print("=" * 115)
print("INTERVALOS DE ALPHA POR CONFIGURACIÓN SELECCIONADA")
print("=" * 115)

for condition in sorted(local_configs):

    scenario, transition = condition

    print()
    print(
        f"{scenario} | {transition}"
    )

    candidates = []

    for key, alphas in intervals.items():

        if key[0] != scenario or key[1] != transition:
            continue

        candidates.append((
            key[2],
            key[3],
            min(alphas),
            max(alphas),
            len(alphas),
        ))

    for kp_f, ki_f, a_min, a_max, n in sorted(candidates):

        print(
            f"  Kp_f={kp_f:.2f}, "
            f"Ki_f={ki_f:.2f} "
            f"-> alpha={a_min:.2f}...{a_max:.2f} "
            f"({n} valores)"
        )

# ------------------------------------------------------------
# Configuración seleccionada en alpha representativo
# ------------------------------------------------------------

print()
print("=" * 115)
print("SELECCIÓN LOCAL EN ALPHAS REPRESENTATIVOS")
print("=" * 115)

for alpha in (0.00, 0.25, 0.50, 0.55, 0.75, 1.00):

    print()
    print(f"ALPHA = {alpha:.2f}")

    for condition in sorted(local_configs):

        candidates = [
            r for r in results
            if r["scenario"] == condition[0]
            and r["transition"] == condition[1]
            and abs(r["alpha_error"] - alpha) < 1e-12
        ]

        if not candidates:
            continue

        # Debe haber una única selección salvo empate exacto.
        r = candidates[0]

        print(
            f"  {condition[0]:18s} "
            f"{condition[1]:20s} "
            f"-> "
            f"({r['kp_factor']:.2f},"
            f"{r['ki_factor']:.2f}) "
            f"MAE={r['mae']:.6f} "
            f"Iq={r['iq_max']:.6f} "
            f"margin={r['current_margin']:.6f}"
        )

# ------------------------------------------------------------
# Número de configuraciones distintas seleccionadas por condición
# ------------------------------------------------------------

print()
print("=" * 115)
print("VARIACIÓN LOCAL DE CONFIGURACIONES")
print("=" * 115)

local_unique = {}

for condition in sorted(local_configs):

    configs_selected = set()

    for key, alphas in intervals.items():

        if key[0] == condition[0] and key[1] == condition[1]:
            configs_selected.add(
                (key[2], key[3])
            )

    local_unique[condition] = configs_selected

    print(
        f"{condition[0]:18s} "
        f"{condition[1]:20s} "
        f"-> {len(configs_selected)} configuraciones"
    )

# ------------------------------------------------------------
# Guardar resultados
# ------------------------------------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

out = OUT_DIR / "b2_5_i_local_selection.csv"

fieldnames = list(results[0].keys())

with out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print()
print(f"Resultado guardado en: {out}")

print()
print("=" * 115)
print("B2.5-I COMPLETADO")
print("=" * 115)
