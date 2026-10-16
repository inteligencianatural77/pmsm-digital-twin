"""Integración cerrada M6 -> M3 -> M4.

Reconstrucción funcional basada en:
- M6 FOC reconstruido desde CloudE/foc_core.
- M3 Electrical Core reconstruido desde CloudE/electrical_core.
- M4 PMSMBase físico existente.

Este archivo NO modifica los módulos originales.
"""

from __future__ import annotations

from pmsm_hybrid_control.foc_reconstructed import FOC
from pmsm_hybrid_control.m3_reconstructed import ElectricalCore
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


def main() -> None:
    # ------------------------------------------------------------
    # Configuración de integración
    # ------------------------------------------------------------
    dt = 50e-6
    steps = 400000
    vdc = 540.0
    omega_ref = 157.079633
    t_load = 0.0

    # ------------------------------------------------------------
    # Módulos recuperados
    # ------------------------------------------------------------
    foc = FOC(
        # Valores del M6 CloudE recuperado
        ld=0.0012,
        lq=0.0012,
        lambda_m=0.107245,
        pole_pairs=4,
        kp_speed=5.2804,
        ki_speed=1.2693,
        ts_current=50e-6,
        ts_speed=200e-6,
        iq_max=112.4300,
        iq_min=-112.4300,
    )

    m3 = ElectricalCore(pole_pairs=4)
    m4 = PMSMBase()

    # ------------------------------------------------------------
    # Estados de feedback iniciales
    # ------------------------------------------------------------
    ia = 0.0
    ib = 0.0
    ic = 0.0

    theta_m = 0.0
    omega_m = 0.0

    # ------------------------------------------------------------
    # Registro mínimo
    # ------------------------------------------------------------
    history: list[dict[str, float]] = []

    print("==================================================")
    print(" CLOSED LOOP — M6 -> M3 -> M4")
    print("==================================================")
    print(f"dt        = {dt}")
    print(f"steps     = {steps}")
    print(f"tiempo    = {steps * dt:.6f} s")
    print(f"VDC       = {vdc:.3f} V")
    print(f"omega_ref = {omega_ref:.6f} rad/s")
    print(f"T_load    = {t_load:.3f} Nm")
    print()

    for k in range(steps):

        # ========================================================
        # Escalon de carga: 0 Nm -> 23 Nm a t = 0.050 s
        # ========================================================
        t = k * dt
        t_load_now = 0.0 if t < 0.050 else 23.0

        # ========================================================
        # M6 — FOC
        # ========================================================
        #
        # Usa las corrientes dq calculadas por M3 en el ciclo
        # anterior.
        #
        vd, vq, id_ref, iq_ref = foc.step(
            omega_ref=omega_ref,
            omega_m=omega_m,
            id_=m3_id if k > 0 else 0.0,
            iq=m3_iq if k > 0 else 0.0,
            vdc=vdc,
            dt=dt,
        )

        # ========================================================
        # M3 — Electrical Core
        # ========================================================
        m3_out = m3.step(
            id_ref=id_ref,
            iq_ref=iq_ref,
            vd_in=vd,
            vq_in=vq,
            ia=ia,
            ib=ib,
            ic=ic,
            theta_m=theta_m,
            omega_m=omega_m,
            vdc=vdc,
            enable_in=True,
        )

        # ========================================================
        # Frontera M3 -> M4
        #
        # CloudE M4:
        #
        # Va = (DUTY_A - 0.5) * VDC
        # Vb = (DUTY_B - 0.5) * VDC
        # Vc = (DUTY_C - 0.5) * VDC
        # ========================================================
        va = (m3_out["DUTY_A"] - 0.5) * vdc
        vb = (m3_out["DUTY_B"] - 0.5) * vdc
        vc = (m3_out["DUTY_C"] - 0.5) * vdc

        # ========================================================
        # M4 — PMSM Base
        # ========================================================
        m4_out = m4.step(
            PlantInput(
                va=va,
                vb=vb,
                vc=vc,
                t_load=t_load_now,
            ),
            dt=dt,
        )

        # ========================================================
        # Feedback M4 -> M3/M6
        # ========================================================
        ia = m4_out.ia
        ib = m4_out.ib
        ic = m4_out.ic

        theta_m = m4_out.theta_m
        omega_m = m4_out.omega_m

        m3_id = m3_out["id"]
        m3_iq = m3_out["iq"]

        # ========================================================
        # Registro
        # ========================================================
        history.append(
            {
                "t": (k + 1) * dt,
                "omega_ref": omega_ref,
                "omega_m": omega_m,
                "theta_m": theta_m,
                "id": m4_out.id,
                "iq": m4_out.iq,
                "id_m3": m3_id,
                "iq_m3": m3_iq,
                "id_ref": id_ref,
                "iq_ref": iq_ref,
                "vd": vd,
                "vq": vq,
                "va": va,
                "vb": vb,
                "vc": vc,
                "duty_a": m3_out["DUTY_A"],
                "duty_b": m3_out["DUTY_B"],
                "duty_c": m3_out["DUTY_C"],
                "te": m4_out.te,
            }
        )

        # --------------------------------------------------------
        # Puntos de trazabilidad
        # --------------------------------------------------------
        if (
            k in (
                0, 1, 2, 3, 9, 99,
                997, 998, 999, 1000, 1001, 1002, 1003,
                1004, 1005, 1009, 1019, 1029, 1049,
                1099, 1199, 1499, 1999,
                39999, 59999, 79999, 99999,
                199999, 299999, 399999
            )
        ):
            print(
                f"k={k:04d} "
                f"w={omega_m:10.4f} "
                f"id={m4_out.id:10.4f} "
                f"iq={m4_out.iq:10.4f} "
                f"iq_ref={iq_ref:10.4f} "
                f"Te={m4_out.te:10.4f} "
                f"Vd={vd:10.4f} "
                f"Vq={vq:10.4f}"
            )

    # ------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------
    final = history[-1]

    # ------------------------------------------------------------
    # Diagnostico interno PI de velocidad — SOLO MEDICION
    # ------------------------------------------------------------
    error_w_final = omega_ref - final["omega_m"]
    p_speed_final = foc.kp_speed * error_w_final
    i_speed_final = foc.ki_speed * foc.int_speed

    print()
    print("==================================================")
    print(" DIAGNOSTICO INTERNO M6 — PI VELOCIDAD")
    print("==================================================")
    print(f"error_w       = {error_w_final:.9f} rad/s")
    print(f"int_speed     = {foc.int_speed:.9f}")
    print(f"Kp*error      = {p_speed_final:.9f} A")
    print(f"Ki*int_speed  = {i_speed_final:.9f} A")
    print(f"iq_ref interno= {foc._iq_ref:.9f} A")
    print(f"speed_counter = {foc.speed_counter}")

    print()
    print("==================================================")
    print(" RESULTADO FINAL")
    print("==================================================")
    print(f"t        = {final['t']:.6f} s")
    print(f"omega_ref= {final['omega_ref']:.6f} rad/s")
    print(f"omega_m  = {final['omega_m']:.6f} rad/s")
    print(f"theta_m  = {final['theta_m']:.6f} rad")
    print(f"id       = {final['id']:.6f} A")
    print(f"iq       = {final['iq']:.6f} A")
    print(f"id_ref   = {final['id_ref']:.6f} A")
    print(f"iq_ref   = {final['iq_ref']:.6f} A")
    print(f"Te       = {final['te']:.6f} Nm")
    print(f"Vd       = {final['vd']:.6f} V")
    print(f"Vq       = {final['vq']:.6f} V")
    print(f"Duty A   = {final['duty_a']:.6f}")
    print(f"Duty B   = {final['duty_b']:.6f}")
    print(f"Duty C   = {final['duty_c']:.6f}")
    print("==================================================")


if __name__ == "__main__":
    main()
