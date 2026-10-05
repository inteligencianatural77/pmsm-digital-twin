"""B1.4 — FOC de corriente cerrado sobre PMSMBase."""

from __future__ import annotations

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


DT = 50e-6
STEPS = 4000

ID_REF = 0.0
IQ_REF = 10.0
T_LOAD = 0.0


def main() -> None:
    plant = PMSMBase()

    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=T_LOAD,
        ),
        dt=DT,
    )

    history = []

    for k in range(STEPS):
        va, vb, vc = foc.step(
            ia=output.ia,
            ib=output.ib,
            ic=output.ic,
            theta_m=output.theta_m,
            omega_m=output.omega_m,
            id_ref=ID_REF,
            iq_ref=IQ_REF,
            dt=DT,
        )

        output = plant.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=T_LOAD,
            ),
            dt=DT,
        )

        history.append(
            {
                "t": (k + 1) * DT,
                "id": output.id,
                "iq": output.iq,
                "omega_m": output.omega_m,
                "theta_m": output.theta_m,
                "te": output.te,
                "va": va,
                "vb": vb,
                "vc": vc,
            }
        )

    last = history[-1]

    print("========================================")
    print(" B1.4 — FOC + PMSMBase")
    print("========================================")
    print(f"dt       = {DT:.9g} s")
    print(f"steps    = {STEPS}")
    print(f"duration = {STEPS * DT:.6f} s")
    print(f"id_ref   = {ID_REF:.6f} A")
    print(f"iq_ref   = {IQ_REF:.6f} A")
    print()
    print(f"id       = {last['id']:.6f} A")
    print(f"iq       = {last['iq']:.6f} A")
    print(f"omega_m  = {last['omega_m']:.6f} rad/s")
    print(f"theta_m  = {last['theta_m']:.6f} rad")
    print(f"Te       = {last['te']:.6f} N*m")
    print()
    print(f"va       = {last['va']:.6f} V")
    print(f"vb       = {last['vb']:.6f} V")
    print(f"vc       = {last['vc']:.6f} V")


if __name__ == "__main__":
    main()
