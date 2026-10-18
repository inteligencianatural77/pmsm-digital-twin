#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_sistema_completo.py

Verifica las 2 capas Sugeno:
  - Capa 1: 7 reglas (fricción)
  - Capa 2: 9 reglas (adaptación de ganancias)
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# =====================================================================
# PARÁMETROS DEL ESCENARIO
# =====================================================================
Tc = 0.50
Ts = 0.80
omega_s = 10.0
delta = 2.0
B = 0.010

Kp0 = 5.2804
Ki0 = 1.2693

# =====================================================================
# FUNCIONES DE PERTENENCIA
# =====================================================================
def z_shape(x, a, b):
    y = np.ones_like(x, dtype=float)
    y[x <= a] = 1.0
    y[x >= b] = 0.0
    mask = (x > a) & (x < b)
    y[mask] = 1.0 - (x[mask] - a) / (b - a)
    return y

def s_shape(x, a, b):
    y = np.zeros_like(x, dtype=float)
    y[x <= a] = 0.0
    y[x >= b] = 1.0
    mask = (x > a) & (x < b)
    y[mask] = (x[mask] - a) / (b - a)
    return y

def tri_shape(x, a, b, c):
    y = np.zeros_like(x, dtype=float)
    mask_left = (x > a) & (x <= b)
    mask_right = (x > b) & (x < c)
    y[mask_left] = (x[mask_left] - a) / (b - a)
    y[mask_right] = (c - x[mask_right]) / (c - b)
    return y

def gauss(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)

# =====================================================================
# MODELO STRIBECK
# =====================================================================
def stribeck(omega):
    omega = np.asarray(omega, dtype=float)
    sign_omega = np.sign(omega)
    abs_omega = np.abs(omega)
    exp_term = np.exp(-(abs_omega / omega_s) ** delta)
    return (Tc + (Ts - Tc) * exp_term) * sign_omega + B * omega


# =====================================================================
# CAPA 1: COMPENSACIÓN DE FRICCIÓN (7 reglas)
# =====================================================================
def capa1_friccion(omega):
    omega = np.atleast_1d(omega).astype(float)
    T_f_hat = np.zeros_like(omega)
    
    for i, w in enumerate(omega):
        mu = np.array([
            z_shape(np.array([w]), -500, -50)[0],     # NG
            tri_shape(np.array([w]), -100, -50, -10)[0], # NM
            tri_shape(np.array([w]), -50, -10, 0)[0],  # NP
            gauss(np.array([w]), 0, 3)[0],             # C
            tri_shape(np.array([w]), 0, 10, 50)[0],    # PP
            tri_shape(np.array([w]), 10, 50, 100)[0],  # PM
            s_shape(np.array([w]), 50, 500)[0],        # PG
        ])
        
        T = np.array([
            -0.50 + 0.010 * w,
             0.0095 * w - 0.55,
             0.0060 * w - 0.70,
             0.0,
             0.0060 * w + 0.70,
             0.0095 * w + 0.55,
            +0.50 + 0.010 * w,
        ])
        
        total_w = mu.sum()
        T_f_hat[i] = np.sum(mu * T) / total_w if total_w > 1e-9 else 0.0
    
    return T_f_hat


# =====================================================================
# CAPA 2: ADAPTACIÓN DE GANANCIAS (9 reglas)
# =====================================================================
def capa2_adaptacion(e_w, de_w):
    e_w = np.atleast_1d(e_w).astype(float)
    de_w = np.atleast_1d(de_w).astype(float)
    alpha_p = np.zeros_like(e_w)
    alpha_i = np.zeros_like(e_w)
    
    # Matrices de consecuentes (filas: e_w, columnas: de_w)
    # Orden: N, C, P
    AP = np.array([
        [0.7, 0.8, 1.0],  # e_w = N
        [1.0, 1.0, 1.0],  # e_w = C
        [1.0, 1.2, 1.5],  # e_w = P
    ])
    AI = np.array([
        [0.8, 0.9, 1.0],
        [1.0, 1.0, 1.0],
        [1.0, 1.1, 1.2],
    ])
    
    for i in range(len(e_w)):
        e = e_w[i]
        de = de_w[i]
        
        mu_e = np.array([
            z_shape(np.array([e]), -50, -15)[0],
            gauss(np.array([e]), 0, 15)[0],
            s_shape(np.array([e]), 15, 50)[0],
        ])
        
        mu_de = np.array([
            z_shape(np.array([de]), -20, -5)[0],
            gauss(np.array([de]), 0, 5)[0],
            s_shape(np.array([de]), 5, 20)[0],
        ])
        
        # Pesos de las 9 reglas
        W = np.outer(mu_e, mu_de)
        total_W = W.sum()
        
        if total_W > 1e-9:
            alpha_p[i] = np.sum(W * AP) / total_W
            alpha_i[i] = np.sum(W * AI) / total_W
        else:
            alpha_p[i] = 1.0
            alpha_i[i] = 1.0
    
    return alpha_p, alpha_i


# =====================================================================
# VERIFICACIÓN
# =====================================================================
def main():
    print("=" * 60)
    print("VERIFICACION DEL SISTEMA COMPLETO (2 CAPAS)")
    print("=" * 60)
    
    os.makedirs("graficas_tesis", exist_ok=True)
    
    # =================================================================
    # PARTE 1: Capa 1 (fricción)
    # =================================================================
    print("\n[PARTE 1] Capa 1 - Compensacion de friccion")
    omega = np.linspace(-500, 500, 1001)
    T_real = stribeck(omega)
    T_est = capa1_friccion(omega)
    error = T_est - T_real
    err_max_pct = 100 * np.max(np.abs(error)) / np.max(np.abs(T_real))
    err_mean_pct = 100 * np.mean(np.abs(error)) / np.max(np.abs(T_real))
    print(f"  Error maximo:  {err_max_pct:.2f}%")
    print(f"  Error medio:   {err_mean_pct:.2f}%")
    
    if err_max_pct < 15:
        print("  [OK] Capa 1 aceptada")
    else:
        print("  [REVISAR] Capa 1 con error alto")
    
    # =================================================================
    # PARTE 2: Capa 2 (adaptación) - barrido de estados
    # =================================================================
    print("\n[PARTE 2] Capa 2 - Adaptacion de ganancias")
    
    casos = [
        ("Error grande positivo, creciendo", 30, 10),
        ("Error grande positivo, estable",   30, 0),
        ("Error grande negativo, decreciendo", -30, -10),
        ("Error cero",                        0, 0),
        ("Error pequeño positivo",            5, 2),
    ]
    
    print(f"  {'Caso':40s} {'alpha_p':>8s} {'alpha_i':>8s}")
    print("  " + "-" * 58)
    
    resultados_capa2 = []
    for nombre, e, de in casos:
        ap, ai = capa2_adaptacion(e, de)
        ap = float(ap[0])
        ai = float(ai[0])
        resultados_capa2.append((nombre, e, de, ap, ai))
        print(f"  {nombre:40s} {ap:8.3f} {ai:8.3f}")
    
    # =================================================================
    # PARTE 3: Gráficas
    # =================================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # (0,0) Capa 1: Stribeck vs Sugeno
    axes[0, 0].plot(omega, T_real, 'b-', linewidth=2, label='Stribeck real')
    axes[0, 0].plot(omega, T_est, 'r--', linewidth=1.5, label='Capa 1 Sugeno')
    axes[0, 0].set_xlabel(r'$\omega_m$ [rad/s]')
    axes[0, 0].set_ylabel(r'$T_f$ [N.m]')
    axes[0, 0].set_title('Capa 1: Friccion')
    axes[0, 0].legend()
    axes[0, 0].grid(True, linestyle=':', alpha=0.6)
    
    # (0,1) Capa 1: error
    axes[0, 1].plot(omega, error * 1000, 'g-', linewidth=1.5)
    axes[0, 1].axhline(0, color='k', linewidth=0.8, linestyle='--')
    axes[0, 1].set_xlabel(r'$\omega_m$ [rad/s]')
    axes[0, 1].set_ylabel('Error [mN.m]')
    axes[0, 1].set_title(f'Capa 1: Error (max {err_max_pct:.1f}%, medio {err_mean_pct:.2f}%)')
    axes[0, 1].grid(True, linestyle=':', alpha=0.6)
    
    # (1,0) Capa 2: alpha_p vs e_w para distintos de_w
    e_range = np.linspace(-50, 50, 100)
    for de_val in [-15, 0, 15]:
        ap_vals = [float(capa2_adaptacion(e, de_val)[0][0]) for e in e_range]
        axes[1, 0].plot(e_range, ap_vals, linewidth=1.8,
                        label=rf'$\Delta e_\omega$ = {de_val}')
    axes[1, 0].axhline(1.0, color='k', linewidth=0.8, linestyle='--')
    axes[1, 0].set_xlabel(r'$e_\omega$ [rad/s]')
    axes[1, 0].set_ylabel(r'$\alpha_p$')
    axes[1, 0].set_title('Capa 2: Factor $\\alpha_p$ vs error')
    axes[1, 0].legend()
    axes[1, 0].grid(True, linestyle=':', alpha=0.6)
    
    # (1,1) Capa 2: alpha_i vs e_w
    for de_val in [-15, 0, 15]:
        ai_vals = [float(capa2_adaptacion(e, de_val)[1][0]) for e in e_range]
        axes[1, 1].plot(e_range, ai_vals, linewidth=1.8,
                        label=rf'$\Delta e_\omega$ = {de_val}')
    axes[1, 1].axhline(1.0, color='k', linewidth=0.8, linestyle='--')
    axes[1, 1].set_xlabel(r'$e_\omega$ [rad/s]')
    axes[1, 1].set_ylabel(r'$\alpha_i$')
    axes[1, 1].set_title('Capa 2: Factor $\\alpha_i$ vs error')
    axes[1, 1].legend()
    axes[1, 1].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig("graficas_tesis/verificacion_sistema_completo.pdf", bbox_inches='tight')
    plt.savefig("graficas_tesis/verificacion_sistema_completo.png", bbox_inches='tight')
    print(f"\n  Grafica guardada: graficas_tesis/verificacion_sistema_completo.png")
    
    print("\n" + "=" * 60)
    print("VERIFICACION COMPLETA")
    print("=" * 60)


if __name__ == "__main__":
    main()
