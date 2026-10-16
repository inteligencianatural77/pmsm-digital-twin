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
# Agregación global por configuración Kp/Ki
#
# Una configuración es admisible solamente si respeta
# Iq_max <= 79.5 A en TODOS los escenarios/transiciones.
# ------------------------------------------------------------

configs = defaultdict(list)

for r in rows:
    key = (
        float(r["kp_factor"]),
        float(r["ki_factor"]),
    )

    configs[key].append({
        "scenario": r["scenario"],
        "transition": r["transition"],
        "mae": float(r["mae_rad_s"]),
        "rmse": float(r["rmse_rad_s"]),
        "final_error": float(r["final_abs_error_rad_s"]),
        "iq_max": float(r["iq_ref_max_A"]),
        "te_max": float(r["te_max_Nm"]),
    })

if len(configs) != 49:
    raise RuntimeError(
        f"Se esperaban 49 configuraciones Kp/Ki; "
        f"se encontraron {len(configs)}."
    )

admissible = {}

for key, points in configs.items():

    if len(points) != 16:
        raise RuntimeError(
            f"{key}: se esperaban 16 condiciones; "
            f"se encontraron {len(points)}."
        )

    if any(p["iq_max"] > I_MAX for p in points):
        continue

    kp_f, ki_f = key

    admissible[key] = {
        "kp_f": kp_f,
        "ki_f": ki_f,
        "mae_mean": sum(p["mae"] for p in points) / len(points),
        "rmse_mean": sum(p["rmse"] for p in points) / len(points),
        "final_mean": sum(p["final_error"] for p in points) / len(points),
        "mae_max": max(p["mae"] for p in points),
        "rmse_max": max(p["rmse"] for p in points),
        "final_max": max(p["final_error"] for p in points),
        "iq_max": max(p["iq_max"] for p in points),
        "te_max": max(p["te_max"] for p in points),
    }

print("=" * 110)
print("B2.5-H — ANÁLISIS MULTICRITERIO")
print("=" * 110)
print(f"Configuraciones totales:     {len(configs)}")
print(f"Configuraciones admisibles:  {len(admissible)}")
print()

if len(admissible) != 14:
    raise RuntimeError(
        f"Se esperaban 14 configuraciones admisibles; "
        f"se encontraron {len(admissible)}."
    )

# ------------------------------------------------------------
# Normalización min-max
#
# Se calcula sobre las 14 configuraciones globalmente admisibles.
# ------------------------------------------------------------

def minmax(values):
    lo = min(values.values())
    hi = max(values.values())

    if hi == lo:
        return {k: 0.0 for k in values}

    return {
        k: (v - lo) / (hi - lo)
        for k, v in values.items()
    }


mae_values = {
    k: v["mae_mean"]
    for k, v in admissible.items()
}

iq_values = {
    k: v["iq_max"]
    for k, v in admissible.items()
}

mae_norm = minmax(mae_values)
iq_norm = minmax(iq_values)

for k, v in admissible.items():
    v["mae_norm"] = mae_norm[k]
    v["iq_norm"] = iq_norm[k]

# ------------------------------------------------------------
# Barrido del peso alpha
#
# J = alpha * MAE_norm + (1-alpha) * Iq_norm
#
# alpha = 0.00 ... 1.00 en pasos de 0.05
# ------------------------------------------------------------

selection_rows = []

for i in range(21):

    alpha = i / 20.0

    scored = []

    for k, v in admissible.items():

        score = (
            alpha * v["mae_norm"]
            +
            (1.0 - alpha) * v["iq_norm"]
        )

        scored.append((score, k, v))

    best_score = min(x[0] for x in scored)

    winners = [
        x for x in scored
        if abs(x[0] - best_score) < 1e-12
    ]

    # Si hay empate exacto, se conservan todos.
    for score, k, v in winners:

        selection_rows.append({
            "alpha_error": alpha,
            "kp_factor": v["kp_f"],
            "ki_factor": v["ki_f"],
            "score": score,
            "mae_mean": v["mae_mean"],
            "iq_max": v["iq_max"],
            "current_margin": I_MAX - v["iq_max"],
            "rmse_mean": v["rmse_mean"],
            "final_error_mean": v["final_mean"],
            "mae_max": v["mae_max"],
            "rmse_max": v["rmse_max"],
            "final_error_max": v["final_max"],
            "te_max": v["te_max"],
        })

# ------------------------------------------------------------
# Mostrar selección
# ------------------------------------------------------------

print("=" * 110)
print("SELECCIÓN SEGÚN PRIORIDAD ERROR / CORRIENTE")
print("=" * 110)

print(
    f"{'alpha':>7} "
    f"{'Kp_f':>6} "
    f"{'Ki_f':>6} "
    f"{'Score':>11} "
    f"{'MAE':>11} "
    f"{'Iqmax':>11} "
    f"{'Margen':>11} "
    f"{'RMSE':>11}"
)

for r in selection_rows:

    print(
        f"{r['alpha_error']:7.2f} "
        f"{r['kp_factor']:6.2f} "
        f"{r['ki_factor']:6.2f} "
        f"{r['score']:11.6f} "
        f"{r['mae_mean']:11.6f} "
        f"{r['iq_max']:11.6f} "
        f"{r['current_margin']:11.6f} "
        f"{r['rmse_mean']:11.6f}"
    )

# ------------------------------------------------------------
# Intervalos de alpha por configuración seleccionada
# ------------------------------------------------------------

winner_by_alpha = {}

for r in selection_rows:
    alpha = r["alpha_error"]
    winner_by_alpha.setdefault(alpha, []).append(
        (r["kp_factor"], r["ki_factor"])
    )

intervals = defaultdict(list)

for alpha, winners in winner_by_alpha.items():

    for winner in winners:
        intervals[winner].append(alpha)

print()
print("=" * 110)
print("RANGO DISCRETO DE ALPHA EN EL QUE CADA CONFIGURACIÓN RESULTA SELECCIONADA")
print("=" * 110)

for config, alphas in sorted(intervals.items()):

    print(
        f"Kp_f={config[0]:.2f}, "
        f"Ki_f={config[1]:.2f} -> "
        f"alpha={min(alphas):.2f} ... {max(alphas):.2f} "
        f"({len(alphas)} valores)"
    )

# ------------------------------------------------------------
# Configuraciones de referencia
# ------------------------------------------------------------

best_mae = min(
    admissible.values(),
    key=lambda v: (v["mae_mean"], v["iq_max"])
)

best_margin = min(
    admissible.values(),
    key=lambda v: (-(
        I_MAX - v["iq_max"]
    ), v["mae_mean"])
)

best_rmse = min(
    admissible.values(),
    key=lambda v: (v["rmse_mean"], v["iq_max"])
)

print()
print("=" * 110)
print("REFERENCIAS DENTRO DEL CONJUNTO ADMISIBLE")
print("=" * 110)

print(
    f"Menor MAE medio:    "
    f"Kp_f={best_mae['kp_f']:.2f}, "
    f"Ki_f={best_mae['ki_f']:.2f}, "
    f"MAE={best_mae['mae_mean']:.6f}, "
    f"Iqmax={best_mae['iq_max']:.6f} A"
)

print(
    f"Mayor margen:       "
    f"Kp_f={best_margin['kp_f']:.2f}, "
    f"Ki_f={best_margin['ki_f']:.2f}, "
    f"Margen={I_MAX-best_margin['iq_max']:.6f} A, "
    f"MAE={best_margin['mae_mean']:.6f}"
)

print(
    f"Menor RMSE medio:   "
    f"Kp_f={best_rmse['kp_f']:.2f}, "
    f"Ki_f={best_rmse['ki_f']:.2f}, "
    f"RMSE={best_rmse['rmse_mean']:.6f}, "
    f"Iqmax={best_rmse['iq_max']:.6f} A"
)

# ------------------------------------------------------------
# Guardar resultados derivados
# ------------------------------------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

out = OUT_DIR / "b2_5_h_multicriteria_selection.csv"

fieldnames = list(selection_rows[0].keys())

with out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(selection_rows)

print()
print(f"Resultado guardado en: {out}")

print()
print("=" * 110)
print("B2.5-H COMPLETADO")
print("=" * 110)
