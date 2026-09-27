#!/usr/bin/env python3
"""
LAZO CERRADO PMSM + FOC
Reconstrucción basada en:

  M3  -> conexiones eléctricas / transformaciones / duty
  M6  -> FOC chart_66.xml
  M4  -> PMSM chart_80.xml

NO modifica ni depende de skeleton.slx.

Modelo promedio, Ts = 50 us.
Primera corrida: réplica de parámetros del skeleton/CloudE.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path

import numpy as np


# ============================================================
# PARAMETROS — REFERENCIA SKELETON
# ============================================================

@dataclass
class Params:
    # Electrical
    Rs: float = 0.0500
    Ld: float = 0.001200
    Lq: float = 0.001200

    # Skeleton/CloudE reference
    lambda_m: float = 0.1100

    # Mechanical
    P: int = 4
    J: float = 0.004160
    B: float = 0.0010
    T_fric: float = 0.50

    # DC bus
    VDC: float = 600.0

    # Sampling
    Ts_c: float = 50e-6
    Ts_s: float = 200e-6

    # Current controller
    Kp_id: float = 15.0796
    Ki_id: float = 628.3185
    Kp_iq: float = 15.0796
    Ki_iq: float = 628.3185

    # Speed controller
    Kp_w: float = 5.2804
    Ki_w: float = 1.2693

    # Exact skeleton limit
    iq_max: float = 112.4300
    iq_min: float = -112.4300

    @property
    def Vmax(self) -> float:
        return max(1.0, self.VDC) / math.sqrt(3.0) * 0.95


# ============================================================
# M3 — ELECTRICAL CORE
# ============================================================

class M3Electrical:
    """
    Replica las conexiones recuperadas de chart_33.xml.

    Clarke:
        i_alpha = ia
        i_beta  = (ia + 2 ib)/sqrt(3)

    Park:
        id = alpha*cos(theta_e) + beta*sin(theta_e)
        iq = -alpha*sin(theta_e) + beta*cos(theta_e)

    Inverse Park + phase reconstruction:
        V_alpha/V_beta -> Va/Vb/Vc

    Duty:
        D = 0.5 + Vphase/VDC
        clamp [0,1]
    """

    def measure_currents(
        self,
        ia: float,
        ib: float,
        ic: float,
        theta_m: float,
        P: int,
    ) -> tuple[float, float, float, float]:

        theta_e = P * theta_m

        i_alpha = ia
        i_beta = (ia + 2.0 * ib) / math.sqrt(3.0)

        c = math.cos(theta_e)
        s = math.sin(theta_e)

        id_ = i_alpha * c + i_beta * s
        iq = -i_alpha * s + i_beta * c

        return id_, iq, theta_e, P

    def voltage_to_duty(
        self,
        Vd: float,
        Vq: float,
        theta_e: float,
        VDC: float,
    ) -> tuple[float, float, float, float, float, float]:

        c = math.cos(theta_e)
        s = math.sin(theta_e)

        # Inverse Park — exactamente la convención de M3
        V_alpha = Vd * c - Vq * s
        V_beta = Vd * s + Vq * c

        # Inverse Clarke — M3
        Va = V_alpha
        Vb = (-V_alpha + math.sqrt(3.0) * V_beta) / 2.0
        Vc = (-V_alpha - math.sqrt(3.0) * V_beta) / 2.0

        # M3 duty
        if abs(VDC) < 1e-12:
            raise ZeroDivisionError("VDC no puede ser cero")

        Da_raw = 0.5 + Va / VDC
        Db_raw = 0.5 + Vb / VDC
        Dc_raw = 0.5 + Vc / VDC

        Da = max(0.0, min(1.0, Da_raw))
        Db = max(0.0, min(1.0, Db_raw))
        Dc = max(0.0, min(1.0, Dc_raw))

        return Da, Db, Dc, Va, Vb, Vc


# ============================================================
# FOC — chart_66.xml RECUPERADO
# ============================================================

class FOC:
    """
    Réplica funcional del foc_core recuperado de chart_66.xml.

    Entradas:
        omega_ref, omega_m, id, iq, VDC

    Salidas:
        Vd, Vq, id_ref, iq_ref
    """

    def __init__(self, p: Params):
        self.p = p

        self.int_id = 0.0
        self.int_iq = 0.0
        self.int_w = 0.0

        self.count_speed = 0
        self.iq_ref_state = 0.0

    def step(
        self,
        omega_ref: float,
        omega_m: float,
        id_: float,
        iq: float,
        VDC: float,
    ) -> tuple[float, float, float, float, bool]:

        p = self.p

        Vmax = max(1.0, VDC) / math.sqrt(3.0) * 0.95

        # ----------------------------------------------------
        # SPEED LOOP — Ts_s = 200 us
        # ----------------------------------------------------

        self.count_speed += 1

        speed_updated = False

        if self.count_speed >= max(
            1,
            round(p.Ts_s / p.Ts_c)
        ):
            self.count_speed = 0
            speed_updated = True

            error_w = omega_ref - omega_m

            self.int_w += error_w * p.Ts_s

            iq_ref_raw = (
                p.Kp_w * error_w
                + p.Ki_w * self.int_w
            )

            iq_ref = max(
                p.iq_min,
                min(p.iq_max, iq_ref_raw)
            )

            if iq_ref != iq_ref_raw:
                self.int_w -= error_w * p.Ts_s

            self.iq_ref_state = iq_ref

        iq_ref_out = self.iq_ref_state

        # ----------------------------------------------------
        # CURRENT LOOP
        # ----------------------------------------------------

        id_ref_out = 0.0

        error_id = id_ref_out - id_
        error_iq = iq_ref_out - iq

        self.int_id += error_id * p.Ts_c
        self.int_iq += error_iq * p.Ts_c

        omega_e = p.P * omega_m

        # d-axis decoupling
        Vd_raw = (
            p.Kp_id * error_id
            + p.Ki_id * self.int_id
            - omega_e * p.Lq * iq
        )

        # q-axis back-EMF compensation
        Vq_raw = (
            p.Kp_iq * error_iq
            + p.Ki_iq * self.int_iq
            + omega_e * (p.Ld * id_ + p.lambda_m)
        )

        # Exact skeleton behavior:
        # independent Vd/Vq saturation
        Vd = max(-Vmax, min(Vmax, Vd_raw))
        Vq = max(-Vmax, min(Vmax, Vq_raw))

        # Anti-windup rollback
        if Vd != Vd_raw:
            self.int_id -= error_id * p.Ts_c

        if Vq != Vq_raw:
            self.int_iq -= error_iq * p.Ts_c

        return (
            Vd,
            Vq,
            id_ref_out,
            iq_ref_out,
            speed_updated,
        )


# ============================================================
# M4 — PMSM MODEL
# ============================================================

class M4PMSM:
    """
    Réplica de chart_80.xml.

    Estados:
        id
        iq
        omega_m
        theta_m
    """

    def __init__(self, p: Params):
        self.p = p

        self.id = 0.0
        self.iq = 0.0
        self.omega_m = 0.0
        self.theta_m = 0.0

    def step(
        self,
        duty_a: float,
        duty_b: float,
        duty_c: float,
        VDC: float,
        Tload: float,
    ) -> dict[str, float]:

        p = self.p

        # ----------------------------------------------------
        # Duty -> phase voltage
        # ----------------------------------------------------

        Va = (duty_a - 0.5) * VDC
        Vb = (duty_b - 0.5) * VDC
        Vc = (duty_c - 0.5) * VDC

        theta_e = p.P * self.theta_m
        omega_e = p.P * self.omega_m

        # ----------------------------------------------------
        # abc -> alpha beta
        # Exact M4 equations
        # ----------------------------------------------------

        V_alpha = (2.0 * Va - Vb - Vc) / 3.0
        V_beta = (Vb - Vc) / math.sqrt(3.0)

        c = math.cos(theta_e)
        s = math.sin(theta_e)

        # ----------------------------------------------------
        # alpha beta -> dq
        # ----------------------------------------------------

        Vd = V_alpha * c + V_beta * s
        Vq = -V_alpha * s + V_beta * c

        # ----------------------------------------------------
        # Electrical dynamics
        # ----------------------------------------------------

        did = (
            Vd
            - p.Rs * self.id
            + omega_e * p.Lq * self.iq
        ) / p.Ld

        diq = (
            Vq
            - p.Rs * self.iq
            - omega_e * (
                p.Ld * self.id
                + p.lambda_m
            )
        ) / p.Lq

        # Euler — exact numerical structure of M4
        self.id += did * p.Ts_c
        self.iq += diq * p.Ts_c

        # ----------------------------------------------------
        # Electromagnetic torque
        # ----------------------------------------------------

        Te = (
            1.5
            * p.P
            * p.lambda_m
            * self.iq
        )

        # Ld = Lq in this model, reluctance term = 0
        # ----------------------------------------------------
        # Mechanical dynamics
        # ----------------------------------------------------

        friction = p.T_fric * np.sign(self.omega_m)

        domega = (
            Te
            - Tload
            - p.B * self.omega_m
            - friction
        ) / p.J

        self.omega_m += domega * p.Ts_c
        self.theta_m += self.omega_m * p.Ts_c

        # ----------------------------------------------------
        # dq -> alpha beta -> abc currents
        # ----------------------------------------------------

        i_alpha = (
            self.id * c
            - self.iq * s
        )

        i_beta = (
            self.id * s
            + self.iq * c
        )

        ia = i_alpha
        ib = (-i_alpha + math.sqrt(3.0) * i_beta) / 2.0
        ic = (-i_alpha - math.sqrt(3.0) * i_beta) / 2.0

        return {
            "ia": ia,
            "ib": ib,
            "ic": ic,
            "id": self.id,
            "iq": self.iq,
            "theta_m": self.theta_m,
            "omega_m": self.omega_m,
            "omega_e": omega_e,
            "Te": Te,
            "Vd_plant": Vd,
            "Vq_plant": Vq,
        }


# ============================================================
# LAZO CERRADO
# ============================================================

def run(
    duration_s: float = 3.0,
    omega_ref: float = 157.0796326795,
    VDC: float = 600.0,
    load_step_time: float = 1.0,
    load_after: float = 23.0,
) -> list[dict[str, float]]:

    p = Params(VDC=VDC)

    m3 = M3Electrical()
    foc = FOC(p)
    m4 = M4PMSM(p)

    steps = int(round(duration_s / p.Ts_c))

    # Inicialización de mediciones
    ia = 0.0
    ib = 0.0
    ic = 0.0

    rows = []

    # Últimas referencias del FOC
    id_ref = 0.0
    iq_ref = 0.0

    # Últimas tensiones
    Vd = 0.0
    Vq = 0.0

    for k in range(steps):

        t = k * p.Ts_c

        # ----------------------------------------------------
        # LOAD STEP — referencia recuperada
        # ----------------------------------------------------

        Tload = 0.0 if t < load_step_time else load_after

        # ----------------------------------------------------
        # M3 — medición abc -> dq
        # ----------------------------------------------------

        id_meas, iq_meas, theta_e, _ = m3.measure_currents(
            ia,
            ib,
            ic,
            m4.theta_m,
            p.P,
        )

        # ----------------------------------------------------
        # FOC
        # ----------------------------------------------------

        (
            Vd,
            Vq,
            id_ref,
            iq_ref,
            speed_updated,
        ) = foc.step(
            omega_ref=omega_ref,
            omega_m=m4.omega_m,
            id_=id_meas,
            iq=iq_meas,
            VDC=VDC,
        )

        # ----------------------------------------------------
        # M3 — Vdq -> duty
        # ----------------------------------------------------

        (
            duty_a,
            duty_b,
            duty_c,
            Va,
            Vb,
            Vc,
        ) = m3.voltage_to_duty(
            Vd,
            Vq,
            theta_e,
            VDC,
        )

        # ----------------------------------------------------
        # M4 — PMSM
        # ----------------------------------------------------

        plant = m4.step(
            duty_a=duty_a,
            duty_b=duty_b,
            duty_c=duty_c,
            VDC=VDC,
            Tload=Tload,
        )

        # ----------------------------------------------------
        # REALIMENTACION
        # ----------------------------------------------------

        ia = plant["ia"]
        ib = plant["ib"]
        ic = plant["ic"]

        # ----------------------------------------------------
        # REGISTRO
        # ----------------------------------------------------

        rows.append({
            "t": t,
            "omega_ref": omega_ref,
            "omega_m": plant["omega_m"],
            "omega_error": omega_ref - plant["omega_m"],
            "id_ref": id_ref,
            "iq_ref": iq_ref,
            "id": plant["id"],
            "iq": plant["iq"],
            "Vd": Vd,
            "Vq": Vq,
            "Va": Va,
            "Vb": Vb,
            "Vc": Vc,
            "duty_a": duty_a,
            "duty_b": duty_b,
            "duty_c": duty_c,
            "ia": ia,
            "ib": ib,
            "ic": ic,
            "Te": plant["Te"],
            "Tload": Tload,
            "theta_m": plant["theta_m"],
            "theta_e": theta_e,
            "VDC": VDC,
            "Vmax": p.Vmax,
            "speed_update": float(speed_updated),
        })

    return rows


# ============================================================
# REPORTE
# ============================================================

def save_csv(rows: list[dict[str, float]], path: Path) -> None:

    if not rows:
        return

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


def print_report(rows: list[dict[str, float]]) -> None:

    r0 = rows[0]
    rf = rows[-1]

    def get_at_time(target: float) -> dict[str, float]:
        return min(
            rows,
            key=lambda r: abs(r["t"] - target)
        )

    r1 = get_at_time(1.0)
    r2 = get_at_time(1.1)

    print()
    print("=" * 70)
    print(" LAZO CERRADO PMSM + M3 + FOC + M4")
    print("=" * 70)

    print(f"t inicial       : {r0['t']:.6f} s")
    print(f"t final         : {rf['t']:.6f} s")

    print()
    print("--- INICIAL ---")
    print(f"omega_m         : {r0['omega_m']:.6f} rad/s")
    print(f"id              : {r0['id']:.6f} A")
    print(f"iq              : {r0['iq']:.6f} A")
    print(f"Te              : {r0['Te']:.6f} Nm")

    print()
    print("--- CARGA t = 1 s ---")
    print(f"omega_m         : {r1['omega_m']:.6f} rad/s")
    print(f"iq_ref          : {r1['iq_ref']:.6f} A")
    print(f"iq              : {r1['iq']:.6f} A")
    print(f"Te              : {r1['Te']:.6f} Nm")
    print(f"Tload           : {r1['Tload']:.6f} Nm")

    print()
    print("--- t = 1.1 s ---")
    print(f"omega_m         : {r2['omega_m']:.6f} rad/s")
    print(f"iq_ref          : {r2['iq_ref']:.6f} A")
    print(f"iq              : {r2['iq']:.6f} A")
    print(f"Te              : {r2['Te']:.6f} Nm")

    print()
    print("--- FINAL ---")
    print(f"omega_m         : {rf['omega_m']:.6f} rad/s")
    print(f"omega_ref       : {rf['omega_ref']:.6f} rad/s")
    print(f"error omega     : {rf['omega_error']:.6f} rad/s")
    print(f"id              : {rf['id']:.6f} A")
    print(f"iq              : {rf['iq']:.6f} A")
    print(f"iq_ref          : {rf['iq_ref']:.6f} A")
    print(f"Te              : {rf['Te']:.6f} Nm")

    print()
    print("--- TENSION ---")
    print(f"Vd              : {rf['Vd']:.6f} V")
    print(f"Vq              : {rf['Vq']:.6f} V")
    print(f"Vmax            : {rf['Vmax']:.6f} V")

    print()
    print("--- DUTY ---")
    print(f"DUTY_A          : {rf['duty_a']:.6f}")
    print(f"DUTY_B          : {rf['duty_b']:.6f}")
    print(f"DUTY_C          : {rf['duty_c']:.6f}")

    print("=" * 70)


def main() -> None:

    base = Path(__file__).resolve().parent

    rows = run()

    csv_path = base / "resultado_lazo_cerrado.csv"

    save_csv(rows, csv_path)
    print_report(rows)

    print()
    print(f"CSV guardado en:")
    print(f"  {csv_path}")


if __name__ == "__main__":
    main()
