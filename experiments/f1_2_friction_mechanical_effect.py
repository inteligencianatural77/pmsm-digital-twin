import csv
from pathlib import Path

from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.pmsm_with_friction import (
    PMSMWithFriction,
)


# ============================================================
# F1.2 — VERIFICACIÓN DEL EFECTO MECÁNICO DE LA FRICCIÓN
# ============================================================
#
# Objetivo:
#
#   verificar de forma aislada que la variante mecánica satisface:
#
#       domega_base - domega_fric = Tf / J
#
# utilizando EXACTAMENTE el mismo estado electromecánico para
# ambas evaluaciones.
#
# Esto evita atribuir a la fricción diferencias que realmente
# provengan de cambios en Te, id, iq u otros estados.
#
# Los parámetros de fricción son exclusivamente de escenario
# experimental.
# NO son parámetros confirmados del Siemens 1FT7087.
# ============================================================

DT = 50e-6
T_END = 0.050

TC = 0.50
TS = 0.80
OMEGA_S = 10.0
DELTA = 2.0
B = 0.01

OUTPUT = Path(
    "experiments/f1_2_friction_mechanical_effect.csv"
)


def main():
    friction_params = StribeckFrictionParameters(
        tc=TC,
        ts=TS,
        omega_s=OMEGA_S,
        delta=DELTA,
        b=B,
    )

    friction = StribeckFriction(friction_params)

    # La variante se utiliza únicamente como portadora del
    # modelo electromecánico y del término de fricción.
    plant = PMSMWithFriction(friction=friction)

    # Estado inicial controlado.
    plant._omega_m = 100.0

    rows = []

    steps = int(round(T_END / DT))

    for k in range(steps + 1):
        t = k * DT

        # Estado actual compartido.
        omega_m = plant._omega_m
        omega_e = plant.params.n_pole_pairs * omega_m

        # Torque electromagnético correspondiente al mismo estado.
        te = plant.electromagnetic_torque()

        t_load = 0.0

        # ----------------------------------------------------
        # Derivada mecánica sin fricción
        # ----------------------------------------------------
        domega_base = (
            te - t_load
        ) / plant.params.j

        # ----------------------------------------------------
        # Derivada mecánica con fricción
        # ----------------------------------------------------
        tf = friction.torque(omega_m)

        domega_friction = (
            te - t_load - tf
        ) / plant.params.j

        # ----------------------------------------------------
        # Verificación directa
        # ----------------------------------------------------
        measured_difference = (
            domega_base - domega_friction
        )

        expected_difference = (
            tf / plant.params.j
        )

        difference_error = (
            measured_difference - expected_difference
        )

        rows.append(
            {
                "t_s": t,
                "omega_m_rad_s": omega_m,
                "omega_e_rad_s": omega_e,
                "te_Nm": te,
                "t_load_Nm": t_load,
                "friction_torque_Nm": tf,
                "domega_without_friction_rad_s2": domega_base,
                "domega_with_friction_rad_s2": domega_friction,
                "domega_difference_rad_s2": measured_difference,
                "expected_difference_rad_s2": expected_difference,
                "difference_error_rad_s2": difference_error,
            }
        )

        # ----------------------------------------------------
        # Evolución de referencia
        #
        # Para recorrer la ley temporalmente usamos la dinámica
        # con fricción. No se pretende aquí reproducir un ensayo
        # FOC; solamente recorrer la variante mecánica.
        # ----------------------------------------------------
        if k < steps:
            d_omega = domega_friction
            plant._omega_m += d_omega * DT
            plant._theta_m += omega_m * DT

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "t_s",
                "omega_m_rad_s",
                "omega_e_rad_s",
                "te_Nm",
                "t_load_Nm",
                "friction_torque_Nm",
                "domega_without_friction_rad_s2",
                "domega_with_friction_rad_s2",
                "domega_difference_rad_s2",
                "expected_difference_rad_s2",
                "difference_error_rad_s2",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    max_error = max(
        abs(row["difference_error_rad_s2"])
        for row in rows
    )

    final = rows[-1]

    print("========================================")
    print(" F1.2 — FRICTION MECHANICAL EFFECT")
    print("========================================")
    print(f"dt          = {DT:.8f} s")
    print(f"duration    = {T_END:.6f} s")
    print(f"steps       = {steps}")
    print()
    print("FRICTION SCENARIO")
    print("----------------------------------------")
    print(f"Tc          = {TC:.6f} N*m")
    print(f"Ts          = {TS:.6f} N*m")
    print(f"omega_s     = {OMEGA_S:.6f} rad/s")
    print(f"delta       = {DELTA:.6f}")
    print(f"B           = {B:.6f} N*m*s/rad")
    print()
    print("INITIAL CONDITION")
    print("----------------------------------------")
    print("omega_m     = 100.000000 rad/s")
    print("T_load      = 0.000000 N*m")
    print()
    print("FINAL STATE")
    print("----------------------------------------")
    print(
        f"omega_m     = "
        f"{final['omega_m_rad_s']:.9f} rad/s"
    )
    print(
        f"Tf          = "
        f"{final['friction_torque_Nm']:.9f} N*m"
    )
    print()
    print("FINAL ACCELERATION DIFFERENCE")
    print("----------------------------------------")
    print(
        f"measured    = "
        f"{final['domega_difference_rad_s2']:.9f} rad/s^2"
    )
    print(
        f"expected    = "
        f"{final['expected_difference_rad_s2']:.9f} rad/s^2"
    )
    print(
        f"error       = "
        f"{final['difference_error_rad_s2']:.3e} rad/s^2"
    )
    print()
    print("GLOBAL VERIFICATION")
    print("----------------------------------------")
    print(
        "max |measured - expected| = "
        f"{max_error:.3e} rad/s^2"
    )
    print()
    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
