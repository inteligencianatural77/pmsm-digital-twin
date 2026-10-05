"""B2.4 — Inspección del integrador del PI de velocidad."""

from __future__ import annotations

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
T_END = 0.200
STEPS = int(T_END / DT)

ID_REF = 0.0
OMEGA_REF = 100.0

LOAD_LEVELS = [
    (0.000, 0.0),
    (0.100, 5.0),
    (0.150, 10.0),
    (0.175, 5.0),
]


def load_reference(t: float) -> float:
    value = 0.0

    for t0, load in LOAD_LEVELS:
        if t >= t0:
            value = load

    return value


def main() -> None:
    plant = PMSMBase()

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController()

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=0.0,
        ),
        dt=DT,
    )

    samples = [
        0.050,
        0.099,
        0.100,
        0.105,
        0.110,
        0.120,
        0.140,
        0.150,
        0.155,
        0.160,
        0.170,
        0.175,
        0.180,
        0.190,
        0.199,
    ]

    results = []

    for k in range(STEPS):
        t = (k + 1) * DT
        t_load = load_reference(t)

        iq_ref = speed_controller.update(
            omega_ref=OMEGA_REF,
            omega_meas=output.omega_m,
            dt=DT,
        )

        va, vb, vc = foc.step(
            ia=output.ia,
            ib=output.ib,
            ic=output.ic,
            theta_m=output.theta_m,
            omega_m=output.omega_m,
            id_ref=ID_REF,
            iq_ref=iq_ref,
            dt=DT,
        )

        output = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=t_load,
            ),
            dt=DT,
        )

        if any(abs(t - ts) < DT / 2 for ts in samples):
            results.append(
                (
                    t,
                    t_load,
                    output.omega_m,
                    OMEGA_REF - output.omega_m,
                    speed_controller.int_w,
                    iq_ref,
                    output.iq,
                    output.te,
                )
            )

    print("========== B2.4 — INTEGRADOR PI VELOCIDAD ==========")
    print(
        "t [s] | Tload | omega | error | int_w | "
        "Iq_ref | Iq | Te"
    )
    print("-" * 95)

    for r in results:
        print(
            f"{r[0]:7.3f} | "
            f"{r[1]:5.1f} | "
            f"{r[2]:9.4f} | "
            f"{r[3]:9.4f} | "
            f"{r[4]:10.6f} | "
            f"{r[5]:9.4f} | "
            f"{r[6]:8.4f} | "
            f"{r[7]:8.4f}"
        )

    print("\n========== ESTADO FINAL ==========")
    print(f"omega_m = {output.omega_m:.6f} rad/s")
    print(f"error   = {OMEGA_REF - output.omega_m:.6f} rad/s")
    print(f"int_w   = {speed_controller.int_w:.6f}")
    print(f"iq_ref  = {speed_controller.iq_ref_state:.6f} A")


if __name__ == "__main__":
    main()
