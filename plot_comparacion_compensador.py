#!/usr/bin/env python3
"""Genera figuras comparativas pi_solo vs pi_capa1."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path("graficas_tesis")
plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

regimenes = ['alta', 'baja', 'reversion']
nombres = {'alta': 'Alta velocidad (50 rad/s)', 
           'baja': 'Baja velocidad (5 rad/s)',
           'reversion': 'Reversión (±20 rad/s)'}

fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=False)

for i, regimen in enumerate(regimenes):
    df_solo = pd.read_csv(OUTPUT_DIR / f"compensador_{regimen}_pi_solo.csv")
    df_capa1 = pd.read_csv(OUTPUT_DIR / f"compensador_{regimen}_pi_capa1.csv")
    
    axes[i].plot(df_solo['t']*1000, df_solo['omega_ref'], 'k--', linewidth=1.5, label='Referencia')
    axes[i].plot(df_solo['t']*1000, df_solo['omega_m'], 'b-', linewidth=1.5, label='PI solo')
    axes[i].plot(df_capa1['t']*1000, df_capa1['omega_m'], 'r-', linewidth=1.5, label='PI + compensación')
    axes[i].set_ylabel(r'$\omega_m$ [rad/s]')
    axes[i].set_title(nombres[regimen])
    axes[i].legend(loc='lower right')
    axes[i].grid(True, linestyle=':', alpha=0.6)

axes[-1].set_xlabel('Tiempo [ms]')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "fig_comparacion_compensador.pdf", bbox_inches='tight')
plt.savefig(OUTPUT_DIR / "fig_comparacion_compensador.png", bbox_inches='tight')
print("Guardado: fig_comparacion_compensador.pdf/.png")

# Figura 2: error
fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=False)
for i, regimen in enumerate(regimenes):
    df_solo = pd.read_csv(OUTPUT_DIR / f"compensador_{regimen}_pi_solo.csv")
    df_capa1 = pd.read_csv(OUTPUT_DIR / f"compensador_{regimen}_pi_capa1.csv")
    
    e_solo = df_solo['omega_ref'] - df_solo['omega_m']
    e_capa1 = df_capa1['omega_ref'] - df_capa1['omega_m']
    
    axes[i].plot(df_solo['t']*1000, e_solo, 'b-', linewidth=1.2, label='PI solo')
    axes[i].plot(df_capa1['t']*1000, e_capa1, 'r-', linewidth=1.2, label='PI + compensación')
    axes[i].axhline(0, color='k', linewidth=0.8, linestyle='--')
    axes[i].set_ylabel('Error [rad/s]')
    axes[i].set_title(nombres[regimen])
    axes[i].legend(loc='upper right')
    axes[i].grid(True, linestyle=':', alpha=0.6)

axes[-1].set_xlabel('Tiempo [ms]')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "fig_error_compensador.pdf", bbox_inches='tight')
plt.savefig(OUTPUT_DIR / "fig_error_compensador.png", bbox_inches='tight')
print("Guardado: fig_error_compensador.pdf/.png")
