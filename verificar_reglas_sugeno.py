#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_reglas_sugeno.py

Verifica que las 7 reglas Sugeno de la Capa 1 (fricción)
reproducen fielmente la curva Stribeck del escenario base.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# =====================================================================
# PARÁMETROS DEL ESCENARIO STRIBECK (supuestos de modelado)
# =====================================================================
Tc = 0.50       # Nm (Coulomb)
Ts = 0.80       # Nm (Stribeck)
omega_s = 10.0  # rad/s (velocidad característica)
delta = 2.0     # exponente
B = 0.010       # Nm·s/rad (viscoso)

# =====================================================================
# MODELO STRIBECK ANALÍTICO
# =====================================================================
def stribeck(omega):
    """Curva Stribeck del escenario base."""
    omega = np.asarray(omega, dtype=float)
    sign_omega = np.sign(omega)
    abs_omega = np.abs(omega)
    
    # Evitar división por cero en omega=0
    exp_term = np.exp(-(abs_omega / omega_s) ** delta)
    
    # Fricción Stribeck + viscosa
    T_f = (Tc + (Ts - Tc) * exp_term) * sign_omega + B * omega
    return T_f

# =====================================================================
# FUNCIONES DE PERTENENCIA (7 conjuntos)
# =====================================================================
def z_shape(x, a, b):
    """Z-shape: 1 en a, 0 en b."""
    y = np.ones_like(x, dtype=float)
    y[x <= a] = 1.0
    y[x >= b] = 0.0
    mask = (x > a) & (x < b)
    y[mask] = 1.0 - (x[mask] - a) / (b - a)
    return y

def s_shape(x, a, b):
    """S-shape: 0 en a, 1 en b."""
    y = np.zeros_like(x, dtype=float)
    y[x <= a] = 0.0
    y[x >= b] = 1.0
    mask = (x > a) & (x < b)
    y[mask] = (x[mask] - a) / (b - a)
    return y

def tri_shape(x, a, b, c):
    """Triangular: 0 en a, 1 en b, 0 en c."""
    y = np.zeros_like(x, dtype=float)
    mask_left = (x > a) & (x <= b)
    mask_right = (x > b) & (x < c)
    y[mask_left] = (x[mask_left] - a) / (b - a)
    y[mask_right] = (c - x[mask_right]) / (c - b)
    return y

def gauss(x, mu, sigma):
    """Gaussiana."""
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)


# =====================================================================
# SISTEMA SUGENO (7 reglas)
# =====================================================================
def sugeno_friccion(omega):
    """
    Sistema Sugeno con 7 reglas para estimar T_f.
    
    Reglas:
      R1: NG (ω < -50)   -> T_f = -0.50 + 0.010·ω
      R2: NM (-100 a -10)-> T_f = 0.0095·ω - 0.55
      R3: NP (-50 a 0)   -> T_f = 0.0060·ω - 0.70
      R4: C  (|ω| < 5)   -> T_f = 0
      R5: PP (0 a 50)    -> T_f = 0.0060·ω + 0.70
      R6: PM (10 a 100)  -> T_f = 0.0095·ω + 0.55
      R7: PG (ω > 50)    -> T_f = +0.50 + 0.010·ω
    """
    omega = np.atleast_1d(omega).astype(float)
    T_f_hat = np.zeros_like(omega)
    
    for i, w in enumerate(omega):
        # 1. Calcular grados de pertenencia de cada conjunto
        mu_NG = z_shape(np.array([w]), -500, -50)[0]
        mu_NM = tri_shape(np.array([w]), -100, -50, -10)[0]
        mu_NP = tri_shape(np.array([w]), -50, -10, 0)[0]
        mu_C  = gauss(np.array([w]), 0, 3)[0]
        mu_PP = tri_shape(np.array([w]), 0, 10, 50)[0]
        mu_PM = tri_shape(np.array([w]), 10, 50, 100)[0]
        mu_PG = s_shape(np.array([w]), 50, 500)[0]
        
        # 2. Consecuentes lineales (Sugeno)
        T_NG = -0.50 + 0.010 * w
        T_NM =  0.0095 * w - 0.55
        T_NP =  0.0060 * w - 0.70
        T_C  =  0.0
        T_PP =  0.0060 * w + 0.70
        T_PM =  0.0095 * w + 0.55
        T_PG = +0.50 + 0.010 * w
        
        # 3. Defuzzificación por promedio ponderado
        weights = np.array([mu_NG, mu_NM, mu_NP, mu_C, mu_PP, mu_PM, mu_PG])
        consequents = np.array([T_NG, T_NM, T_NP, T_C, T_PP, T_PM, T_PG])
        
        total_w = weights.sum()
        if total_w < 1e-9:
            T_f_hat[i] = 0.0
        else:
            T_f_hat[i] = np.sum(weights * consequents) / total_w
    
    return T_f_hat


# =====================================================================
# VERIFICACIÓN
# =====================================================================
def main():
    print("=" * 60)
    print("VERIFICACIÓN DE LAS 7 REGLAS SUGENO vs STRIBECK")
    print("=" * 60)
    
    # Rango de evaluación
    omega = np.linspace(-500, 500, 1001)
    
    # Curva real (Stribeck)
    T_real = stribeck(omega)
    
    # Curva estimada (Sugeno)
    T_est = sugeno_friccion(omega)
    
    # Métricas de error
    error = T_est - T_real
    error_max = np.max(np.abs(error))
    error_mean = np.mean(np.abs(error))
    error_rmse = np.sqrt(np.mean(error**2))
    T_max = np.max(np.abs(T_real))
    error_max_pct = 100 * error_max / T_max
    error_mean_pct = 100 * error_mean / T_max
    
    print(f"\nRango de T_f real: [{np.min(T_real):.3f}, {np.max(T_real):.3f}] Nm")
    print(f"\nError máximo absoluto:  {error_max:.4f} Nm")
    print(f"Error medio absoluto:   {error_mean:.4f} Nm")
    print(f"Error RMSE:             {error_rmse:.4f} Nm")
    print(f"\nError máximo relativo:  {error_max_pct:.2f}%")
    print(f"Error medio relativo:   {error_mean_pct:.2f}%")
    
    # Veredicto
    if error_max_pct < 10:
        print("\n✅ APROBADO: error máximo < 10%")
    elif error_max_pct < 20:
        print("\n⚠️ ACEPTABLE: error máximo entre 10% y 20%")
    else:
        print("\n❌ RECHAZADO: error máximo > 20% (ajustar coeficientes)")
    
    # Guardar CSV
    os.makedirs("graficas_tesis", exist_ok=True)
    import csv
    with open("graficas_tesis/verificacion_sugeno.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["omega", "T_real", "T_est", "error"])
        for w, tr, te, e in zip(omega, T_real, T_est, error):
            writer.writerow([w, tr, te, e])
    print("\nCSV guardado: graficas_tesis/verificacion_sugeno.csv")
    
    # Gráfica
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    axes[0].plot(omega, T_real, 'b-', linewidth=2, label='Stribeck real')
    axes[0].plot(omega, T_est, 'r--', linewidth=1.5, label='Sugeno (7 reglas)')
    axes[0].set_xlabel(r'$\omega_m$ [rad/s]')
    axes[0].set_ylabel(r'$T_f$ [N·m]')
    axes[0].set_title('Comparación: Stribeck real vs Sugeno (7 reglas)')
    axes[0].legend()
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    axes[1].plot(omega, error * 1000, 'g-', linewidth=1.5)
    axes[1].axhline(0, color='k', linewidth=0.8, linestyle='--')
    axes[1].set_xlabel(r'$\omega_m$ [rad/s]')
    axes[1].set_ylabel('Error [mN·m]')
    axes[1].set_title(f'Error (máx: {error_max*1000:.1f} mN·m, medio: {error_mean*1000:.1f} mN·m)')
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig("graficas_tesis/verificacion_sugeno.pdf", bbox_inches='tight')
    plt.savefig("graficas_tesis/verificacion_sugeno.png", bbox_inches='tight')
    print("Gráfica guardada: graficas_tesis/verificacion_sugeno.png")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
