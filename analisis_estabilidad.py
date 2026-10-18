#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_estabilidad.py

Análisis de estabilidad del lazo cerrado FOC+PI+compensador Sugeno.
Usa control + slycot.
"""

import numpy as np
import matplotlib.pyplot as plt
import control as ct
from pathlib import Path

# =====================================================================
# PARÁMETROS
# =====================================================================
RS = 0.05
LD = 1.2e-3
LQ = 1.2e-3
LAMBDA_M = 0.107245
P_POLES = 4
J = 41.6e-4
B_VISC = 0.010

KP_W = 5.2804
KI_W = 1.2693

K_COMP = 0.0058
B_COMP = 0.70

OMEGA_M_OP = 5.0

OUTPUT_DIR = Path("graficas_tesis")
OUTPUT_DIR.mkdir(exist_ok=True)


# =====================================================================
# MODELO LINEALIZADO
# =====================================================================
def modelo_planta_linealizado():
    omega_e = P_POLES * OMEGA_M_OP
    
    A = np.array([
        [-RS/LD,            omega_e*LQ/LD,       0],
        [-omega_e*LD/LQ,    -RS/LQ,              -P_POLES*LAMBDA_M/LQ],
        [0,                 1.5*P_POLES*LAMBDA_M/J,  -(B_VISC + K_COMP)/J],
    ])
    
    B = np.array([
        [1/LD, 0,    0],
        [0,    1/LQ, 0],
        [0,    0,    -1/J],
    ])
    
    C = np.array([[0, 0, 1]])
    D = np.zeros((1, 3))
    
    return ct.ss(A, B, C, D)


# =====================================================================
# ANÁLISIS
# =====================================================================
def main():
    print("=" * 60)
    print("ANÁLISIS DE ESTABILIDAD — FOC+PI+COMPENSADOR")
    print("=" * 60)
    print(f"Punto de operación: omega_m = {OMEGA_M_OP} rad/s")
    print()
    
    planta = modelo_planta_linealizado()
    
    # Polos de la planta
    poles_planta = ct.poles(planta)
    print("Polos de la planta (lazo abierto):")
    for p in poles_planta:
        print(f"  {p:.4f}  |{abs(p):.2f}|")
    print()
    
    # TF de la planta: vq → omega_m
    # Usar la entrada 1 (vq) y salida 0 (omega_m)
    planta_tf = ct.tf(planta[0, 1])
    print("Función de transferencia de la planta (vq -> omega_m):")
    print(planta_tf)
    print()
    
    # PI velocidad
    C_w = ct.tf([KP_W, KI_W], [1, 0])
    print("Controlador PI velocidad:")
    print(C_w)
    print()
    
    # Lazo abierto
    L = C_w * planta_tf
    print("Lazo abierto L(s) = C(s) * G(s):")
    print(L)
    print()
    
    # Márgenes
    print("=" * 60)
    print("MÁRGENES DE ESTABILIDAD")
    print("=" * 60)
    try:
        gm, pm, wg, wp = ct.margin(L)
        print(f"Margen de ganancia: {20*np.log10(gm):.2f} dB")
        print(f"Margen de fase:     {pm:.2f}°")
        print(f"Frecuencia de cruce de ganancia: {wg:.2f} rad/s")
        print(f"Frecuencia de cruce de fase:     {wp:.2f} rad/s")
    except Exception as e:
        print(f"Error calculando márgenes: {e}")
    print()
    
    # Polos del lazo cerrado
    T = ct.feedback(L, 1)
    poles_cl = ct.poles(T)
    estable = all(p.real < 0 for p in poles_cl)
    print("=" * 60)
    print("POLOS DEL LAZO CERRADO")
    print("=" * 60)
    for p in poles_cl:
        print(f"  {p:.4f}  |{abs(p):.2f}|")
    print(f"\nSistema {'ESTABLE' if estable else 'INESTABLE'}")
    print()
    
    # =================================================================
    # FIGURA 1: LUGAR DE RAÍCES
    # =================================================================
    fig1, ax1 = plt.subplots(figsize=(10, 8))
    ct.root_locus(L, plot=True)
    plt.title('Lugar de raíces del lazo de velocidad')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "estabilidad_root_locus.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "estabilidad_root_locus.png", bbox_inches='tight')
    plt.close()
    print("Guardado: estabilidad_root_locus.pdf/.png")
    
    # =================================================================
    # FIGURA 2: BODE
    # =================================================================
    fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ct.bode_plot(L, dB=True, Hz=False, plot=True)
    plt.suptitle('Diagrama de Bode del lazo abierto')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "estabilidad_bode.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "estabilidad_bode.png", bbox_inches='tight')
    plt.close()
    print("Guardado: estabilidad_bode.pdf/.png")
    
    # =================================================================
    # FIGURA 3: RESPUESTA AL ESCALÓN
    # =================================================================
    t = np.linspace(0, 0.5, 1000)
    t_out, y_out = ct.step_response(T, T=t)
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(t_out * 1000, y_out, 'b-', linewidth=1.5)
    ax3.axhline(1.0, color='k', linestyle='--', linewidth=0.8, label='Referencia')
    ax3.set_xlabel('Tiempo [ms]')
    ax3.set_ylabel('Velocidad [rad/s]')
    ax3.set_title('Respuesta al escalón del lazo cerrado')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "estabilidad_step.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "estabilidad_step.png", bbox_inches='tight')
    plt.close()
    print("Guardado: estabilidad_step.pdf/.png")
    
    print()
    print("=" * 60)
    print("FIN DEL ANÁLISIS")
    print("=" * 60)


if __name__ == "__main__":
    main()
