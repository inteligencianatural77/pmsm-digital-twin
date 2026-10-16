import csv
from pathlib import Path

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)


# ============================================================
# F0.1 — CARACTERIZACIÓN AISLADA DE FRICCIÓN
# ============================================================
#
# Estos valores son exclusivamente de escenario experimental.
# NO son parámetros confirmados del Siemens 1FT7087.
#
# El objetivo es observar la forma de la ley:
#
# Tf(omega) =
#     Tc*sign(omega)
#     + (Ts-Tc)*exp(-(abs(omega)/omega_s)^delta)*sign(omega)
#     + B*omega
#
# antes de integrarla al PMSM.
# ============================================================

TC = 0.50
TS = 0.80
OMEGA_S = 10.0
DELTA = 2.0
B = 0.01

OMEGA_MIN = -100.0
OMEGA_MAX = 100.0
OMEGA_STEP = 0.5

OUTPUT = Path(
    "experiments/f0_1_friction_characterization.csv"
)


def main():
    friction = StribeckFriction(
        StribeckFrictionParameters(
            tc=TC,
            ts=TS,
            omega_s=OMEGA_S,
            delta=DELTA,
            b=B,
        )
    )

    rows = []

    n_steps = int(
        round((OMEGA_MAX - OMEGA_MIN) / OMEGA_STEP)
    )

    for k in range(n_steps + 1):
        omega = OMEGA_MIN + k * OMEGA_STEP
        torque = friction.torque(omega)

        rows.append(
            {
                "omega_m_rad_s": omega,
                "friction_torque_Nm": torque,
            }
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    print("========================================")
    print(" F0.1 — FRICTION CHARACTERIZATION")
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
    print(
        f"Tf(-100)    = "
        f"{friction.torque(-100.0):.9f} N*m"
    )
    print(
        f"Tf(-10)     = "
        f"{friction.torque(-10.0):.9f} N*m"
    )
    print(
        f"Tf(-1)      = "
        f"{friction.torque(-1.0):.9f} N*m"
    )
    print(
        f"Tf(0)       = "
        f"{friction.torque(0.0):.9f} N*m"
    )
    print(
        f"Tf(1)       = "
        f"{friction.torque(1.0):.9f} N*m"
    )
    print(
        f"Tf(10)      = "
        f"{friction.torque(10.0):.9f} N*m"
    )
    print(
        f"Tf(100)     = "
        f"{friction.torque(100.0):.9f} N*m"
    )
    print()
    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
