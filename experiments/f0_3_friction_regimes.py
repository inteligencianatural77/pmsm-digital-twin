import csv
import math
from pathlib import Path

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)


# ============================================================
# F0.3 — IDENTIFICACIÓN DE REGÍMENES DE FRICCIÓN
# ============================================================
#
# Valores de escenario experimental.
# NO son parámetros confirmados del Siemens 1FT7087.
#
# El objetivo es determinar, a partir de la propia ley,
# dónde cambia la contribución relativa de:
#
#   - Coulomb
#   - Stribeck
#   - viscosa
#
# No se introducen umbrales arbitrarios de velocidad.
# ============================================================

TC = 0.50
TS = 0.80
OMEGA_S = 10.0
DELTA = 2.0
B = 0.01

OMEGA_MIN = 0.0
OMEGA_MAX = 100.0
OMEGA_STEP = 0.01

OUTPUT = Path("experiments/f0_3_friction_regimes.csv")


def components(omega_m: float):
    """
    Descompone la ley de fricción para omega >= 0.
    """
    if omega_m < 0.0:
        raise ValueError("F0.3 usa magnitud de velocidad omega >= 0.")

    if omega_m == 0.0:
        coulomb = 0.0
        stribeck = 0.0
    else:
        coulomb = TC
        stribeck = (
            (TS - TC)
            * math.exp(-((omega_m / OMEGA_S) ** DELTA))
        )

    viscous = B * omega_m
    total = coulomb + stribeck + viscous

    return coulomb, stribeck, viscous, total


def relative(value: float, total: float) -> float:
    if total == 0.0:
        return 0.0
    return abs(value) / abs(total)


def find_nearest(rows, key, target):
    return min(rows, key=lambda row: abs(row[key] - target))


def main():
    params = StribeckFrictionParameters(
        tc=TC,
        ts=TS,
        omega_s=OMEGA_S,
        delta=DELTA,
        b=B,
    )

    friction = StribeckFriction(params)

    rows = []

    omega = OMEGA_MIN

    while omega <= OMEGA_MAX + 1e-12:
        coulomb, stribeck, viscous, total = components(omega)

        if omega == 0.0:
            model_total = friction.torque(0.0)
        else:
            model_total = friction.torque(omega)

        rows.append(
            {
                "omega_m_rad_s": omega,
                "coulomb_Nm": coulomb,
                "stribeck_Nm": stribeck,
                "viscous_Nm": viscous,
                "friction_total_Nm": total,
                "stribeck_fraction": relative(stribeck, total),
                "viscous_fraction": relative(viscous, total),
                "model_total_Nm": model_total,
                "model_difference_Nm": total - model_total,
            }
        )

        omega += OMEGA_STEP

    # --------------------------------------------------------
    # Puntos característicos
    # --------------------------------------------------------

    # Velocidad donde Stribeck = viscosa.
    # Se obtiene buscando el mínimo de |Ts_term - B*omega|.
    omega_cross = min(
        rows[1:],
        key=lambda r: abs(r["stribeck_Nm"] - r["viscous_Nm"]),
    )

    # Velocidad donde la contribución Stribeck cae al 10%.
    omega_10pct = min(
        rows[1:],
        key=lambda r: abs(r["stribeck_fraction"] - 0.10),
    )

    # Velocidad donde la contribución Stribeck cae al 5%.
    omega_5pct = min(
        rows[1:],
        key=lambda r: abs(r["stribeck_fraction"] - 0.05),
    )

    # Velocidad donde la contribución viscosa alcanza 50%.
    omega_visc_50 = min(
        rows[1:],
        key=lambda r: abs(r["viscous_fraction"] - 0.50),
    )

    # --------------------------------------------------------
    # Exportación
    # --------------------------------------------------------

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "omega_m_rad_s",
                "coulomb_Nm",
                "stribeck_Nm",
                "viscous_Nm",
                "friction_total_Nm",
                "stribeck_fraction",
                "viscous_fraction",
                "model_total_Nm",
                "model_difference_Nm",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    # --------------------------------------------------------
    # Verificación de consistencia
    # --------------------------------------------------------

    max_difference = max(
        abs(r["model_difference_Nm"])
        for r in rows
    )

    # --------------------------------------------------------
    # Salida
    # --------------------------------------------------------

    print("========================================")
    print(" F0.3 — FRICTION REGIMES")
    print("========================================")
    print(f"Tc          = {TC:.6f} N*m")
    print(f"Ts          = {TS:.6f} N*m")
    print(f"omega_s     = {OMEGA_S:.6f} rad/s")
    print(f"delta       = {DELTA:.6f}")
    print(f"B           = {B:.6f} N*m*s/rad")
    print()
    print(f"omega min   = {OMEGA_MIN:.6f} rad/s")
    print(f"omega max   = {OMEGA_MAX:.6f} rad/s")
    print(f"omega step  = {OMEGA_STEP:.6f} rad/s")
    print(f"points      = {len(rows)}")
    print()
    print("TRANSICIONES IDENTIFICADAS")
    print("----------------------------------------")
    print(
        "Stribeck = viscous:"
        f" {omega_cross['omega_m_rad_s']:.2f} rad/s"
    )
    print(
        "Stribeck ≈ 10% total:"
        f" {omega_10pct['omega_m_rad_s']:.2f} rad/s"
    )
    print(
        "Stribeck ≈ 5% total:"
        f" {omega_5pct['omega_m_rad_s']:.2f} rad/s"
    )
    print(
        "Viscous ≈ 50% total:"
        f" {omega_visc_50['omega_m_rad_s']:.2f} rad/s"
    )
    print()
    print("VALORES EN LAS TRANSICIONES")
    print("----------------------------------------")

    for name, row in [
        ("Stribeck = viscous", omega_cross),
        ("Stribeck ≈ 10%", omega_10pct),
        ("Stribeck ≈ 5%", omega_5pct),
        ("Viscous ≈ 50%", omega_visc_50),
    ]:
        print(name)
        print(
            f"  omega       = {row['omega_m_rad_s']:.2f} rad/s"
        )
        print(
            f"  Coulomb     = {row['coulomb_Nm']:.6f} N*m"
        )
        print(
            f"  Stribeck    = {row['stribeck_Nm']:.6f} N*m"
        )
        print(
            f"  Viscous     = {row['viscous_Nm']:.6f} N*m"
        )
        print(
            f"  Total       = {row['friction_total_Nm']:.6f} N*m"
        )
        print(
            f"  Stribeck %  = "
            f"{100.0 * row['stribeck_fraction']:.3f}%"
        )
        print(
            f"  Viscous %   = "
            f"{100.0 * row['viscous_fraction']:.3f}%"
        )
        print()

    print("VERIFICACIÓN")
    print("----------------------------------------")
    print(
        "Máxima diferencia descomposición/modelo = "
        f"{max_difference:.3e} N*m"
    )

    print()
    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
