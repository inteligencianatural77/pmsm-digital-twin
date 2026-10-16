import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "figure.figsize": (9, 5)
})

OUTPUT_DIR = "graficas_tesis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def guardar(nombre):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.pdf"), format='pdf', bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.png"), format='png', bbox_inches='tight')
    plt.close()

# ==============================================================================
# 1. ENSAYO B2.3: Regulación de velocidad con carga
# ==============================================================================
try:
    df_b23 = pd.read_csv("experiments/b2_3_speed_load_steps.csv")
    fig, ax1 = plt.subplots()
    
    ax1.set_xlabel('Tiempo [s]')
    ax1.set_ylabel(r'Velocidad $\omega_m$ [rad/s]', color='tab:blue')
    ax1.plot(df_b23['t'], df_b23['omega_ref'], 'k--', linewidth=1.5, label=r'Ref. $\omega_m^*$')
    ax1.plot(df_b23['t'], df_b23['omega_m'], color='tab:blue', linewidth=1.5, label=r'$\omega_m$ real')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, linestyle=':', alpha=0.7)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel(r'Corriente $i_q$ [A]', color='tab:red')
    ax2.plot(df_b23['t'], df_b23['iq'], color='tab:red', linewidth=1.2, linestyle='-.', label=r'$i_q$')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')
    
    plt.title('Regulación de velocidad con par de carga (Ensayo B2.3)')
    guardar("fig_b2_3_velocidad_carga_REAL")
    print("✅ Gráfica B2.3 generada con datos reales.")
except Exception as e:
    print(f"❌ Error en B2.3: {e}")

# ==============================================================================
# 2. FRONTERA DE PARETO B2.5 (Barrido de parámetros)
# ==============================================================================
try:
    df_b25 = pd.read_csv("experiments/b2_5_parameter_sweep_metrics.csv")
    
    # Agrupamos por configuración de factores para obtener el peor caso de corriente y el MAE promedio
    grouped = df_b25.groupby(['kp_factor', 'ki_factor']).agg(
        mae_avg=('mae_rad_s', 'mean'),
        max_iq=('iq_ref_max_A', 'max')
    ).reset_index()
    
    plt.figure(figsize=(9, 6))
    
    admisibles = grouped[grouped['max_iq'] <= 79.5]
    no_admisibles = grouped[grouped['max_iq'] > 79.5]
    
    plt.scatter(no_admisibles['max_iq'], no_admisibles['mae_avg'], 
                color='red', alpha=0.5, s=60, label='No admisibles (> 79.5 A)', zorder=1)
    plt.scatter(admisibles['max_iq'], admisibles['mae_avg'], 
                color='green', alpha=0.8, s=70, label='Admisibles (≤ 79.5 A)', zorder=2)
    
    plt.axvline(x=79.5, color='black', linestyle='--', linewidth=1.5, label='Límite físico (79.5 A)')
    
    plt.xlabel(r'Demanda máxima de corriente $|i_q^*|_{\max}$ [A]')
    plt.ylabel('Error Absoluto Medio (MAE) [rad/s]')
    plt.title('Frontera de Pareto: Compromiso Seguimiento vs. Esfuerzo (B2.5)')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc='upper right')
    
    guardar("fig_b2_5_frontera_pareto_REAL")
    print("✅ Gráfica de Pareto B2.5 generada con datos reales.")
except Exception as e:
    print(f"❌ Error en Pareto: {e}")

# ==============================================================================
# 3. SIMULACIÓN ANFIS: Evolución de ganancias y velocidad
# ==============================================================================
try:
    df_anfis = pd.read_csv("experiments/sim_anfis_adaptive.csv")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    
    # Subgráfica 1: Velocidad
    ax1.plot(df_anfis['t'], df_anfis['omega_ref'], 'k--', linewidth=1.2, label=r'Referencia $\omega_m^*$')
    ax1.plot(df_anfis['t'], df_anfis['omega_m'], 'b-', linewidth=1.5, label=r'$\omega_m$ real (ANFIS)')
    ax1.set_ylabel(r'Velocidad [rad/s]')
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.set_title('Respuesta del sistema con adaptación ANFIS')
    
    # Subgráfica 2: Ganancias
    ax2.plot(df_anfis['t'], df_anfis['Kp'], 'r-', linewidth=1.5, label=r'$K_p^{adapt}$')
    ax2.plot(df_anfis['t'], df_anfis['Ki'], 'g-', linewidth=1.5, label=r'$K_i^{adapt}$')
    ax2.set_xlabel('Tiempo [s]')
    ax2.set_ylabel('Ganancias del PI')
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle=':', alpha=0.7)
    
    guardar("fig_anfis_evolucion_ganancias_REAL")
    print("✅ Gráfica de evolución ANFIS generada con datos reales.")
except Exception as e:
    print(f"❌ Error en ANFIS: {e}")

print("\n🎉 ¡LISTO! Revisa la carpeta 'graficas_tesis' para ver los archivos _REAL.pdf")
