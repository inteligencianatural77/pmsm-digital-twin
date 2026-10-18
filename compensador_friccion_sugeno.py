#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compensador_friccion_sugeno.py

Compensador difuso Sugeno de fricción (7 reglas).
Compara 2 modos:
  - 'pi_solo'  : FOC+PI sin compensación
  - 'pi_capa1' : FOC+PI + compensación de fricción

En 3 regímenes:
  - 'alta'      : referencia 50 rad/s
  - 'baja'      : referencia 5 rad/s
  - 'reversion' : 0 → +20 → 0 → -20 → 0 rad/s
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from pmsm_hybrid_control.plant.pmsm_with_friction import PMSMWithFriction
from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.parameters import default_m4_parameters
from pmsm_hybrid_control.plant.pmsm_base import PlantInput

# =====================================================================
# PARÁMETROS
# =====================================================================
TC = 0.50
TS_S = 0.80
OMEGA_S = 10.0
DELTA = 2.0
B_VISC = 0.010

KP0 = 5.2804
KI0 = 1.2693

KP_ID = 15.0796
KI_ID = 300.0
KP_IQ = 15.0796
KI_IQ = 300.0

TS_SIM = 1e-6
TS_SPEED = 200e-6

IQ_MAX = 112.43
V_MAX = 540.0 / np.sqrt(3) * 0.95

OUTPUT_DIR = Path("graficas_tesis")
OUTPUT_DIR.mkdir(exist_ok=True)


# =====================================================================
# FUNCIONES DE PERTENENCIA
# =====================================================================
def z_shape(x, a, b):
    if x <= a: return 1.0
    if x >= b: return 0.0
    return 1.0 - (x - a) / (b - a)


def s_shape(x, a, b):
    if x <= a: return 0.0
    if x >= b: return 1.0
    return (x - a) / (b - a)


def tri_shape(x, a, b, c):
    if x <= a or x >= c: return 0.0
    if x <= b: return (x - a) / (b - a)
    return (c - x) / (c - b)


def gauss(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)


# =====================================================================
# CAPA 1: FRICCIÓN (7 reglas Sugeno)
# =====================================================================
def capa1_friccion(omega):
    mu_NG = z_shape(omega, -500, -50)
    mu_NM = tri_shape(omega, -100, -50, -10)
    mu_NP = tri_shape(omega, -50, -10, 0)
    mu_C  = gauss(omega, 0, 3)
    mu_PP = tri_shape(omega, 0, 10, 50)
    mu_PM = tri_shape(omega, 10, 50, 100)
    mu_PG = s_shape(omega, 50, 500)

    T_NG = -0.50 + 0.010 * omega
    T_NM =  0.0095 * omega - 0.55
    T_NP =  0.0060 * omega - 0.70
    T_C  =  0.0
    T_PP =  0.0060 * omega + 0.70
    T_PM =  0.0095 * omega + 0.55
    T_PG = +0.50 + 0.010 * omega

    W = np.array([mu_NG, mu_NM, mu_NP, mu_C, mu_PP, mu_PM, mu_PG])
    T = np.array([T_NG, T_NM, T_NP, T_C, T_PP, T_PM, T_PG])
    total = W.sum()
    if total < 1e-9:
        return 0.0
    return float(np.sum(W * T) / total)


# =====================================================================
# SIMULACIÓN
# =====================================================================
def simular(modo, regimen, duracion=0.2):
    fp = StribeckFrictionParameters(tc=TC, ts=TS_S, omega_s=OMEGA_S, delta=DELTA, b=B_VISC)
    friction = StribeckFriction(fp)
    plant = PMSMWithFriction(friction=friction)

    def omega_ref_fn(t):
        if regimen == 'alta': return 50.0
        elif regimen == 'baja': return 5.0
        elif regimen == 'reversion':
            if t < 0.05: return 0.0
            elif t < 0.10: return 20.0
            elif t < 0.15: return 0.0
            else: return -20.0
        return 0.0

    integral_state = (0.0, 0.0, 0.0)
    speed_counter = 0
    hist = {k: [] for k in ['t', 'omega_ref', 'omega_m', 'id', 'iq', 'iq_ref',
                             'vd', 'vq', 'Te', 'Tf_hat']}

    t = 0.0
    n_steps = int(duracion / TS_SIM)

    for _ in range(n_steps):
        s = plant.states
        omega_m = s['omega_m']
        id_ = s['id']
        iq = s['iq']
        theta_e = 4.0 * s['theta_m']
        omega_ref = omega_ref_fn(t)

        speed_counter += 1
        do_speed = (speed_counter >= int(TS_SPEED / TS_SIM)) or (len(hist['iq_ref']) == 0)
        if do_speed:
            speed_counter = 0

        Tf_hat = 0.0
        if modo == 'pi_capa1':
            Tf_hat = capa1_friccion(omega_m)

        if do_speed:
            e_w = omega_ref - omega_m
            int_id, int_iq, int_w = integral_state
            int_w_new = int_w + e_w * TS_SPEED
            iq_ref_raw = KP0 * e_w + KI0 * int_w_new + Tf_hat
            iq_ref = np.clip(iq_ref_raw, -IQ_MAX, IQ_MAX)
            if iq_ref != iq_ref_raw:
                int_w_new = int_w
            integral_state = (int_id, int_iq, int_w_new)
        else:
            iq_ref = hist['iq_ref'][-1] if hist['iq_ref'] else 0.0

        e_d = 0.0 - id_
        e_q = iq_ref - iq
        int_id, int_iq, int_w = integral_state
        int_id_new = int_id + e_d * TS_SIM
        int_iq_new = int_iq + e_q * TS_SIM
        omega_e = 4.0 * omega_m
        vd_raw = KP_ID * e_d + KI_ID * int_id_new - omega_e * 0.0012 * iq
        vq_raw = KP_IQ * e_q + KI_IQ * int_iq_new + omega_e * (0.0012 * id_ + 0.107245)
        vd = np.clip(vd_raw, -V_MAX, V_MAX)
        vq = np.clip(vq_raw, -V_MAX, V_MAX)
        if vd != vd_raw: int_id_new = int_id
        if vq != vq_raw: int_iq_new = int_iq
        integral_state = (int_id_new, int_iq_new, int_w)

        cos_te = np.cos(theta_e)
        sin_te = np.sin(theta_e)
        valpha = vd * cos_te - vq * sin_te
        vbeta = vd * sin_te + vq * cos_te
        va = valpha
        vb = -0.5 * valpha + (np.sqrt(3.0) / 2.0) * vbeta
        vc = -0.5 * valpha - (np.sqrt(3.0) / 2.0) * vbeta

        inp = PlantInput(va=va, vb=vb, vc=vc, t_load=0.0)
        out = plant.step(inp, TS_SIM)

        hist['t'].append(t)
        hist['omega_ref'].append(omega_ref)
        hist['omega_m'].append(out.omega_m)
        hist['id'].append(out.id)
        hist['iq'].append(out.iq)
        hist['iq_ref'].append(iq_ref)
        hist['vd'].append(vd)
        hist['vq'].append(vq)
        hist['Te'].append(out.te)
        hist['Tf_hat'].append(Tf_hat)

        t += TS_SIM

    return pd.DataFrame(hist)


# =====================================================================
# MAIN
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("COMPENSADOR SUGENO DE FRICCIÓN")
    print("=" * 60)

    regimenes = ['alta', 'baja', 'reversion']
    modos = ['pi_solo', 'pi_capa1']

    for regimen in regimenes:
        for modo in modos:
            print(f"\nSimulando: regimen={regimen}, modo={modo}")
            df = simular(modo, regimen, duracion=0.2)
            e = df['omega_ref'] - df['omega_m']
            mae = np.mean(np.abs(e))
            rmse = np.sqrt(np.mean(e**2))
            iae = np.trapezoid(np.abs(e), df['t'])
            ise = np.trapezoid(e**2, df['t'])
            print(f"  MAE={mae:.4f}  RMSE={rmse:.4f}  IAE={iae:.4f}  ISE={ise:.4f}")
            out_csv = OUTPUT_DIR / f"compensador_{regimen}_{modo}.csv"
            df.to_csv(out_csv, index=False)
            print(f"  Guardado: {out_csv}")

    print("\n" + "=" * 60)
    print("FIN")
    print("=" * 60)
