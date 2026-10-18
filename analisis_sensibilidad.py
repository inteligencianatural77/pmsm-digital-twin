#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_sensibilidad.py

Análisis de sensibilidad del compensador Sugeno de fricción.
Evalúa cómo cambia el MAE cuando varían los parámetros del motor.

- J: dato real (SIEMENS-DIRECTO), variación por carga acoplada
- B, Tc, Ts, ωs, δ: supuestos de modelado, variación de robustez
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
# PARÁMETROS NOMINALES
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
def simular(params, regimen, modo='pi_capa1', duracion=0.2):
    """Simula con parámetros dados."""
    fp = StribeckFrictionParameters(
        tc=params['tc'], ts=params['ts'], omega_s=params['omega_s'],
        delta=params['delta'], b=params['b']
    )
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
    hist_t = []
    hist_err = []

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
        do_speed = (speed_counter >= int(TS_SPEED / TS_SIM)) or (len(hist_err) == 0)
        if do_speed:
            speed_counter = 0

        Tf_hat = capa1_friccion(omega_m) if modo == 'pi_capa1' else 0.0

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
            iq_ref = 0.0 if not hist_t else iq_ref

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

        err = omega_ref - out.omega_m
        hist_t.append(t)
        hist_err.append(err)
        t += TS_SIM

    return np.mean(np.abs(hist_err))


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("ANÁLISIS DE SENSIBILIDAD DEL COMPENSADOR SUGENO")
    print("=" * 60)

    # Parámetros nominales
    nominal = {'tc': TC, 'ts': TS_S, 'omega_s': OMEGA_S, 'delta': DELTA, 'b': B_VISC}
    # Nota: J no se varía en este script (se haría con default_m4_parameters)

    # Regímenes
    regimenes = ['alta', 'baja', 'reversion']

    # =================================================================
    # BARRIDO 1: Fricción viscosa B (±50%)
    # =================================================================
    print("\n[BARRIDO 1] Fricción viscosa B (±50%)")
    b_values = [B_VISC * 0.5, B_VISC * 0.75, B_VISC, B_VISC * 1.25, B_VISC * 1.5]
    b_results = []
    for b in b_values:
        p = nominal.copy()
        p['b'] = b
        row = {'b': b}
        for reg in regimenes:
            row[reg] = simular(p, reg, 'pi_capa1')
        b_results.append(row)
        print(f"  B={b:.4f}: " + " ".join(f"{reg}={row[reg]:.4f}" for reg in regimenes))

    # =================================================================
    # BARRIDO 2: Par de Coulomb Tc (±50%)
    # =================================================================
    print("\n[BARRIDO 2] Par de Coulomb Tc (±50%)")
    tc_values = [TC * 0.5, TC * 0.75, TC, TC * 1.25, TC * 1.5]
    tc_results = []
    for tc in tc_values:
        p = nominal.copy()
        p['tc'] = tc
        row = {'tc': tc}
        for reg in regimenes:
            row[reg] = simular(p, reg, 'pi_capa1')
        tc_results.append(row)
        print(f"  Tc={tc:.4f}: " + " ".join(f"{reg}={row[reg]:.4f}" for reg in regimenes))

    # =================================================================
    # BARRIDO 3: Par de Stribeck Ts (±50%)
    # =================================================================
    print("\n[BARRIDO 3] Par de Stribeck Ts (±50%)")
    ts_values = [TS_S * 0.75, TS_S * 0.875, TS_S, TS_S * 1.125, TS_S * 1.25]
    ts_results = []
    for ts in ts_values:
        p = nominal.copy()
        p['ts'] = ts
        row = {'ts': ts}
        for reg in regimenes:
            row[reg] = simular(p, reg, 'pi_capa1')
        ts_results.append(row)
        print(f"  Ts={ts:.4f}: " + " ".join(f"{reg}={row[reg]:.4f}" for reg in regimenes))

    # =================================================================
    # EXPORTAR CSV
    # =================================================================
    df_b = pd.DataFrame(b_results)
    df_tc = pd.DataFrame(tc_results)
    df_ts = pd.DataFrame(ts_results)

    df_b.to_csv(OUTPUT_DIR / "sensibilidad_B.csv", index=False)
    df_tc.to_csv(OUTPUT_DIR / "sensibilidad_Tc.csv", index=False)
    df_ts.to_csv(OUTPUT_DIR / "sensibilidad_Ts.csv", index=False)
    print("\nCSVs guardados:")
    print(f"  {OUTPUT_DIR}/sensibilidad_B.csv")
    print(f"  {OUTPUT_DIR}/sensibilidad_Tc.csv")
    print(f"  {OUTPUT_DIR}/sensibilidad_Ts.csv")

    # =================================================================
    # FIGURAS
    # =================================================================
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].plot(df_b['b'], df_b['alta'], 'o-', label='Alta')
    axes[0].plot(df_b['b'], df_b['baja'], 's-', label='Baja')
    axes[0].plot(df_b['b'], df_b['reversion'], '^-', label='Reversión')
    axes[0].set_xlabel('B [Nm·s/rad]')
    axes[0].set_ylabel('MAE [rad/s]')
    axes[0].set_title('Sensibilidad a B')
    axes[0].legend()
    axes[0].grid(True, linestyle=':', alpha=0.6)

    axes[1].plot(df_tc['tc'], df_tc['alta'], 'o-', label='Alta')
    axes[1].plot(df_tc['tc'], df_tc['baja'], 's-', label='Baja')
    axes[1].plot(df_tc['tc'], df_tc['reversion'], '^-', label='Reversión')
    axes[1].set_xlabel('Tc [Nm]')
    axes[1].set_ylabel('MAE [rad/s]')
    axes[1].set_title('Sensibilidad a Tc')
    axes[1].legend()
    axes[1].grid(True, linestyle=':', alpha=0.6)

    axes[2].plot(df_ts['ts'], df_ts['alta'], 'o-', label='Alta')
    axes[2].plot(df_ts['ts'], df_ts['baja'], 's-', label='Baja')
    axes[2].plot(df_ts['ts'], df_ts['reversion'], '^-', label='Reversión')
    axes[2].set_xlabel('Ts [Nm]')
    axes[2].set_ylabel('MAE [rad/s]')
    axes[2].set_title('Sensibilidad a Ts')
    axes[2].legend()
    axes[2].grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sensibilidad_friccion.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "sensibilidad_friccion.png", bbox_inches='tight')
    print(f"\n  {OUTPUT_DIR}/sensibilidad_friccion.png")

    print("\n" + "=" * 60)
    print("FIN")
    print("=" * 60)


if __name__ == "__main__":
    main()
