import csv
import math
from pathlib import Path

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)


# ============================================================
# F0.2 — DESCOMPOSICIÓN DE LA LEY DE FRICCIÓN
# ============================================================
#
# Estos valores son exclusivamente de escenario experimental.
# NO son parámetros confirmados del Siemens 1FT7087.
#
# Se separan las contribuciones:
#
#   1) Coulomb
#   2) Stribeck
#   3) viscosa
#   4) fricción total
#
# para identificar qué término domina en cada régimen.
# ============================================================

TC = 0.50
TS = 0.80
OMEGA_S = 10.0
DELTA = 2.0
B = 0.01

OMEGA_MIN = -100.0
OMEGA_MAX = 100.0
OMEGA_STEP = 0.5

OUTPUT = Path("experiments/f0_2_friction_decomposition.csv")


def sign(x: float) -> float:
    if x > 0.0:
        return 1.0
    if x < 0.0:
        return -1.0
    return 0.0


def components(omega_m: float):
    s = sign(omega_m)

    coulomb = TC * s

    stribeck = (
        (TS - TC)
        * math.exp(-((abs(omega_m) / OMEGA_S) ** DELTA))
        * s
    )

    viscous = B * omega_m

    total = coulomb + stribeck + viscous

    return coulomb, stribeck, viscous, total


def main():
    params = StribeckFrictionParameters(
        tc=TC,
        ts=TS,
        omega_s=OMEGA_S,
        delta=DELTA,
        b=B,
    )

    # Verificación independiente contra la implementación oficial.
    friction = StribeckFriction(params)

    rows = []

    omega = OMEGA_MIN

    while omega <= OMEGA_MAX + 1e-12:
        coulomb, stribeck, viscous, total = components(omega)
        model_total = friction.torque(omega)

        rows.append(
            {
                "omega_m_rad_s": omega,
                "coulomb_Nm": coulomb,
                "stribeck_Nm": stribeck,
                "viscous_Nm": viscous,
                "friction_total_Nm": total,
                "model_total_Nm": model_total,
            }
        )

        omega += OMEGA_STEP

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
                "model_total_Nm",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("========================================")
    print(" F0.2 — FRICTION DECOMPOSITION")
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
    print("REGIMEN REPRESENTATIVO")
    print("----------------------------------------")

    for omega in [-100.0, -10.0, -1.0, 0.0, 1.0, 10.0, 100.0]:
        coulomb, stribeck, viscous, total = components(omega)
        model_total = friction.torque(omega)

        print(f"omega = {omega:8.3f} rad/s")
        print(f"  Coulomb  = {coulomb: .9f} N*m")
        print(f"  Stribeck = {stribeck: .9f} N*m")
        print(f"  Viscous  = {viscous: .9f} N*m")
        print(f"  Total    = {total: .9f} N*m")
        print(f"  Model    = {model_total: .9f} N*m")
        print(f"  diff     = {total - model_total: .3e} N*m")
        print()

    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
