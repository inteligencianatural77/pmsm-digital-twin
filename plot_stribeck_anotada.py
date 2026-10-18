#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_stribeck_anotada.py

Genera la curva Stribeck anotada con las regiones de operación
del robot cartesiano.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path("graficas_tesis")
OUTPUT_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

# =====================================================================
# CARGAR DATOS
# =====================================================================
csv_path = Path("experiments/f0_1_friction_characterization.csv")
if csv_path.exists():
    df = pd.read_csv(csv_path)
    omega = df['omega_m_rad_s'].values
    tf = df['friction_torque_Nm'].values
else:
    # Si no existe, generar la curva con el modelo
    print("CSV no encontrado, generando curva con el modelo Stribeck")
    Tc, Ts, omega_s, delta, B = 0.50, 0.80, 10.0, 2.0, 0.010
    omega = np.linspace(-100, 100, 1000)
    tf = np.where(
        omega == 0, 0,
        (Tc + (Ts - Tc) * np.exp(-(np.abs(omega) / omega_s) ** delta)) * np.sign(omega) + B * omega
    )

# =====================================================================
# FIGURA
# =====================================================================
fig, ax = plt.subplots(figsize=(10, 6))

# Curva Stribeck
ax.plot(omega, tf, 'b-', linewidth=2.5, label='Modelo Stribeck', zorder=5)

# Ejes
ax.axhline(0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
ax.axvline(0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)

# =====================================================================
# REGIONES ANOTADAS
# =====================================================================

# Región A: alta velocidad (|ω| > 50)
ax.axvspan(50, 100, alpha=0.15, color='green', label='Región A: viscosa domina')
ax.axvspan(-100, -50, alpha=0.15, color='green')

# Región B: baja velocidad (10 < |ω| < 50)
ax.axvspan(10, 50, alpha=0.15, color='orange', label='Región B: Stribeck visible')
ax.axvspan(-50, -10, alpha=0.15, color='orange')

# Región C: crítica (|ω| < 10)
ax.axvspan(-10, 10, alpha=0.25, color='red', label='Región C: transición crítica')

# =====================================================================
# ANOTACIONES
# =====================================================================
ax.annotate('Región A\n(viscosa domina)',
            xy=(75, 2.0), fontsize=10, ha='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='lightgreen', alpha=0.7))

ax.annotate('Región B\n(Stribeck visible)',
            xy=(30, 1.2), fontsize=10, ha='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='wheat', alpha=0.7))

ax.annotate('Región C\n(transición crítica)',
            xy=(0, -1.5), fontsize=10, ha='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='lightcoral', alpha=0.7))

# Zona de operación del robot (baja velocidad)
ax.annotate('Zona de operación\ndel robot cartesiano',
            xy=(5, 0.7), xytext=(40, 0.3),
            fontsize=9, ha='left', style='italic',
            arrowprops=dict(arrowstyle='->', color='purple', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', fc='lavender', alpha=0.7))

# =====================================================================
# ESTILO
# =====================================================================
ax.set_xlabel(r'$\omega_m$ [rad/s]')
ax.set_ylabel(r'$T_f$ [N·m]')
ax.set_title('Curva de fricción Stribeck con regiones de operación')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper left', framealpha=0.9)
ax.set_xlim(-100, 100)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "fig_f0_1_friccion_caracterizacion_anotada.pdf", bbox_inches='tight')
plt.savefig(OUTPUT_DIR / "fig_f0_1_friccion_caracterizacion_anotada.png", bbox_inches='tight')
plt.close()
print("Guardado: fig_f0_1_friccion_caracterizacion_anotada.pdf/.png")
