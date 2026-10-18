#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_robustez.py

Análisis de robustez del compensador Sugeno de fricción.
Evalúa el desempeño ante incertidumbre combinada en B, Tc, Ts.

Método: 20 escenarios aleatorios con variación ±30% en (B, Tc, Ts).
Compara: pi_solo vs pi_capa1.
Métrica: mejora porcentual del MAE.
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
            iq_ref = 0.0 if not hist_err else iq_ref

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
        hist_err.append(err)
        t += TS_SIM

    return np.mean(np.abs(hist_err))


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("ANÁLISIS DE ROBUSTEZ DEL COMPENSADOR SUGENO")
    print("=" * 60)
    print("Método: 20 escenarios con variación ±30% en (B, Tc, Ts)")
    print()

    np.random.seed(42)  # reproducibilidad

    # Parámetros nominales
    nominal = {'tc': TC, 'ts': TS_S, 'omega_s': OMEGA_S, 'delta': DELTA, 'b': B_VISC}

    # Regímenes
    regimenes = ['alta', 'baja', 'reversion']

    # =================================================================
    # GENERAR ESCENARIOS
    # =================================================================
    n_scenarios = 20
    variacion = 0.30  # ±30%

    escenarios = []
    for i in range(n_scenarios):
        p = nominal.copy()
        p['b'] = B_VISC * (1 + np.random.uniform(-variacion, variacion))
        p['tc'] = TC * (1 + np.random.uniform(-variacion, variacion))
        p['ts'] = TS_S * (1 + np.random.uniform(-variacion, variacion))
        # Asegurar Ts >= Tc
        if p['ts'] < p['tc']:
            p['ts'] = p['tc'] * 1.1
        escenarios.append(p)

    print(f"Escenarios generados: {n_scenarios}")
    print()

    # =================================================================
    # SIMULAR CADA ESCENARIO
    # =================================================================
    resultados = []
    for i, p in enumerate(escenarios):
        print(f"Escenario {i+1}/{n_scenarios}: B={p['b']:.4f}, Tc={p['tc']:.3f}, Ts={p['ts']:.3f}")
        row = {'escenario': i+1, 'b': p['b'], 'tc': p['tc'], 'ts': p['ts']}
        for reg in regimenes:
            mae_solo = simular(p, reg, 'pi_solo')
            mae_capa1 = simular(p, reg, 'pi_capa1')
            mejora = 100 * (mae_solo - mae_capa1) / mae_solo if mae_solo > 0 else 0
            row[f'{reg}_solo'] = mae_solo
            row[f'{reg}_capa1'] = mae_capa1
            row[f'{reg}_mejora'] = mejora
        resultados.append(row)
        print(f"  Mejoras: " + " ".join(f"{reg}={row[f'{reg}_mejora']:.1f}%" for reg in regimenes))

    # =================================================================
    # EXPORTAR CSV
    # =================================================================
    df = pd.DataFrame(resultados)
    df.to_csv(OUTPUT_DIR / "robustez_escenarios.csv", index=False)
    print(f"\nCSV guardado: {OUTPUT_DIR}/robustez_escenarios.csv")

    # =================================================================
    # TABLA RESUMEN
    # =================================================================
    print("\n" + "=" * 60)
    print("TABLA RESUMEN (mejora porcentual)")
    print("=" * 60)
    print(f"{'Régimen':<15} {'Media':>10} {'Mediana':>10} {'Mín':>10} {'Máx':>10}")
    print("-" * 60)
    for reg in regimenes:
        col = df[f'{reg}_mejora']
        print(f"{reg:<15} {col.mean():>9.1f}% {col.median():>9.1f}% {col.min():>9.1f}% {col.max():>9.1f}%")

    # =================================================================
    # FIGURAS
    # =================================================================
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for i, reg in enumerate(regimenes):
        axes[i].hist(df[f'{reg}_mejora'], bins=10, color='steelblue', edgecolor='black')
        axes[i].axvline(df[f'{reg}_mejora'].mean(), color='red', linestyle='--',
                        label=f'Media: {df[f"{reg}_mejora"].mean():.1f}%')
        axes[i].set_xlabel('Mejora del MAE [%]')
        axes[i].set_ylabel('Frecuencia')
        axes[i].set_title(f'Régimen: {reg}')
        axes[i].legend()
        axes[i].grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "robustez_histograma.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "robustez_histograma.png", bbox_inches='tight')
    print(f"\nFigura guardada: {OUTPUT_DIR}/robustez_histograma.png")

    print("\n" + "=" * 60)
    print("FIN")
    print("=" * 60)


if __name__ == "__main__":
    main()
