#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_twin_cap3.py

Regenera las 3 figuras del Capitulo 3 (Gemelo digital):
  - fig_twin_anclas_operacion.pdf/.png
  - fig_twin_consistencia_parametros.pdf/.png
  - fig_twin_respuesta_dinamica.pdf/.png

Uso: python3 plot_twin_cap3.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================================
# ESTILO (consistente con generar_graficas.py y la tesis)
# =====================================================================
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "figure.figsize": (8, 5),
})

OUTPUT_DIR = "graficas_tesis"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def guardar(nombre):
    """Guarda una figura en PDF y PNG."""
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.pdf"),
                format='pdf', bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.png"),
                format='png', bbox_inches='tight')
    plt.close()
    print(f"  OK: {nombre}.pdf/.png")


# =====================================================================
# FIG. 3.3 — Anclas de operacion
# =====================================================================
def fig_anclas_operacion():
    """Grafica los 3 puntos ancla documentados en el manual Siemens."""
    # Puntos del manual Siemens (Tabla 7.3)
    puntos = {
        'Par de bloqueo':      {'rpm': 0,    'Nm': 61,  'color': 'tab:blue'},
        'Punto nominal':       {'rpm': 4500, 'Nm': 46,  'color': 'tab:green'},
        'Par maximo (pub.)':   {'rpm': None, 'Nm': 150, 'color': 'tab:red'},
    }

    fig, ax = plt.subplots(figsize=(9, 5.5))

    # Graficar solo los puntos con rpm definido
    for nombre, p in puntos.items():
        if p['rpm'] is not None:
            ax.scatter(p['rpm'], p['Nm'], s=120, color=p['color'],
                       edgecolor='black', linewidth=0.8, zorder=3,
                       label=nombre)
            ax.annotate(f"{nombre}\n{p['Nm']} N·m @ {p['rpm']} rpm",
                        xy=(p['rpm'], p['Nm']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=10)

    # Nota sobre par maximo sin velocidad
    ax.scatter([], [], s=120, color='tab:red', edgecolor='black',
               linewidth=0.8, label='Par maximo publicado: 150 N·m')
    ax.annotate('Par maximo publicado: 150 N·m\n(velocidad no especificada)',
                xy=(0.98, 0.75), xycoords='axes fraction',
                ha='right', va='top', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.4', fc='lightyellow',
                          ec='gray', lw=0.8))

    ax.set_xlabel('Velocidad [rpm]')
    ax.set_ylabel('Par [N·m]')
    ax.set_title('Puntos de referencia documentados del PMSM')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_xlim(-300, 5000)
    ax.set_ylim(30, 170)
    ax.legend(loc='lower right', framealpha=0.95)

    fig.text(0.5, -0.02,
             'Los marcadores representan valores documentados. '
             'No se interpola una curva continua.',
             ha='center', fontsize=9, style='italic', color='gray')

    guardar("fig_twin_anclas_operacion")


# =====================================================================
# FIG. 3.4 — Consistencia de parametros
# =====================================================================
def fig_consistencia_parametros():
    """Barras horizontales con los 3 errores relativos."""
    categorias = [
        'Potencia nominal',
        'Par de bloqueo',
        'Constante electrica',
    ]
    errores = [0.11, 0.05, 0.33]
    colores = ['tab:blue', 'tab:green', 'tab:orange']
    referencia = 0.5

    fig, ax = plt.subplots(figsize=(9, 4.5))

    y_pos = np.arange(len(categorias))
    bars = ax.barh(y_pos, errores, color=colores,
                   edgecolor='black', linewidth=0.6, height=0.6)

    # Etiquetas con el valor
    for bar, err in zip(bars, errores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{err:.2f} %', va='center', fontsize=10)

    ax.axvline(referencia, color='gray', linestyle='--',
               linewidth=1.2, label=f'Referencia {referencia} %')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categorias)
    ax.set_xlabel('Diferencia relativa [%]')
    ax.set_title('Consistencia matematica de los parametros del PMSM')
    ax.set_xlim(0, 0.6)
    ax.grid(True, axis='x', linestyle=':', alpha=0.6)
    ax.legend(loc='lower right')

    fig.text(0.5, -0.02,
             'Errores calculados a partir de los valores del capitulo; '
             'no constituyen medicion experimental.',
             ha='center', fontsize=9, style='italic', color='gray')

    guardar("fig_twin_consistencia_parametros")


# =====================================================================
# FIG. 3.5 — Respuesta dinamica (B2.3)
# =====================================================================
def fig_respuesta_dinamica():
    """3 subplots del ensayo B2.3."""
    df = pd.read_csv('experiments/b2_3_speed_load_steps.csv')

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)

    # Subplot 1: Velocidad
    axes[0].plot(df['t']*1000, df['omega_ref'], 'k--',
                 linewidth=1.4, label=r'Referencia $\omega_m^*$')
    axes[0].plot(df['t']*1000, df['omega_m'], 'b-',
                 linewidth=1.5, label=r'Velocidad $\omega_m$')
    axes[0].set_ylabel(r'Velocidad [rad/s]')
    axes[0].legend(loc='lower right')
    axes[0].grid(True, linestyle=':', alpha=0.6)
    axes[0].set_title('Respuesta del PMSM ante escalones de carga (B2.3)')

    # Subplot 2: Par
    axes[1].plot(df['t']*1000, df['te'], 'b-',
                 linewidth=1.3, label=r'Par electromagnetico $T_e$')
    axes[1].plot(df['t']*1000, df['t_load'], color='orange', linewidth=1.5,
                 label=r'Par de carga $T_{load}$')
    axes[1].set_ylabel(r'Par [N·m]')
    axes[1].legend(loc='lower right')
    axes[1].grid(True, linestyle=':', alpha=0.6)

    # Subplot 3: Corriente iq
    axes[2].plot(df['t']*1000, df['iq'], 'b-',
                 linewidth=1.3, label=r'$i_q$')
    axes[2].plot(df['t']*1000, df['iq_ref'], 'r--',
                 linewidth=1.1, label=r'$i_q^*$')
    axes[2].set_xlabel('Tiempo [ms]')
    axes[2].set_ylabel(r'Corriente $i_q$ [A]')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, linestyle=':', alpha=0.6)

    fig.text(0.5, -0.01,
             'Simulacion con paso 50 us. '
             'Resultados no constituyen validacion experimental.',
             ha='center', fontsize=9, style='italic', color='gray')

    guardar("fig_twin_respuesta_dinamica")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("Generando figuras del Capitulo 3 (Gemelo Digital)")
    print("=" * 60)

    print("\n[1/3] Anclas de operacion...")
    fig_anclas_operacion()

    print("\n[2/3] Consistencia de parametros...")
    fig_consistencia_parametros()

    print("\n[3/3] Respuesta dinamica (B2.3)...")
    fig_respuesta_dinamica()

    print("\n" + "=" * 60)
    print(f"Figuras generadas en: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
