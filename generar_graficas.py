import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuración profesional para tesis
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
    "figure.figsize": (8, 5)
})

OUTPUT_DIR = "graficas_tesis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def guardar_figura(nombre_archivo):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre_archivo}.pdf"), format='pdf', bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre_archivo}.png"), format='png', bbox_inches='tight')
    plt.close()

def plot_friccion():
    try:
        df = pd.read_csv("experiments/f0_1_friction_characterization.csv")
        plt.figure()
        plt.plot(df['omega_m_rad_s'], df['friction_torque_Nm'], 'b-', linewidth=2, label='Par de fricción $T_f$')
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.xlabel('Velocidad mecánica $\omega_m$ [rad/s]')
        plt.ylabel('Par de fricción $T_f$ [N·m]')
        plt.title('Caracterización del modelo de fricción no lineal (Stribeck)')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        guardar_figura("fig_f0_1_friccion_caracterizacion")
        print("✅ Gráfica de fricción generada.")
    except Exception as e:
        print(f"⚠️ Error en fricción: {e}")

def plot_seguimiento_corriente():
    try:
        df = pd.read_csv("experiments/b1_5_iq_reference_steps.csv")
        plt.figure()
        plt.plot(df['t'], df['iq_ref'], 'r--', linewidth=1.5, label='Referencia $i_q^*$')
        plt.plot(df['t'], df['iq'], 'b-', linewidth=1.2, label='Corriente real $i_q$')
        plt.xlabel('Tiempo [s]')
        plt.ylabel('Corriente de cuadratura [A]')
        plt.title('Seguimiento de referencias escalonadas de corriente (B1.5)')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        guardar_figura("fig_b1_5_seguimiento_iq")
        print("✅ Gráfica de seguimiento de corriente generada.")
    except Exception as e:
        print(f"⚠️ Error en seguimiento de corriente: {e}")

def plot_velocidad_con_carga():
    try:
        df = pd.read_csv("experiments/b2_3_speed_load_steps.csv")
        fig, ax1 = plt.subplots()
        
        ax1.set_xlabel('Tiempo [s]')
        ax1.set_ylabel('Velocidad $\omega_m$ [rad/s]', color='tab:blue')
        ax1.plot(df['t'], df['omega_ref'], 'k--', linewidth=1.5, label='Ref. $\omega_m^*$')
        ax1.plot(df['t'], df['omega_m'], color='tab:blue', linewidth=1.5, label='$\omega_m$ real')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.grid(True, linestyle=':', alpha=0.7)
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('Corriente $i_q$ [A]', color='tab:red')
        ax2.plot(df['t'], df['iq'], color='tab:red', linewidth=1.2, linestyle='-.', label='$i_q$')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')
        
        plt.title('Regulación de velocidad con par de carga (B2.3)')
        guardar_figura("fig_b2_3_velocidad_carga")
        print("✅ Gráfica de velocidad con carga generada.")
    except Exception as e:
        print(f"⚠️ Error en velocidad con carga: {e}")

def plot_comparacion_friccion():
    try:
        df = pd.read_csv("experiments/f1_3_foc_pi_friction_comparison.csv")
        plt.figure()
        plt.plot(df['t'], df['omega_base'], 'b-', linewidth=1.5, label='Sin fricción')
        plt.plot(df['t'], df['omega_friction'], 'r-', linewidth=1.5, label='Con fricción (Base)')
        plt.plot(df['t'], df['omega_ref'], 'k--', linewidth=1.2, label='Referencia $\omega_m^*$')
        
        plt.xlabel('Tiempo [s]')
        plt.ylabel('Velocidad $\omega_m$ [rad/s]')
        plt.title('Efecto de la fricción no lineal en la respuesta de velocidad (F1.3)')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        guardar_figura("fig_f1_3_comparacion_friccion")
        print("✅ Gráfica de comparación de fricción generada.")
    except Exception as e:
        print(f"⚠️ Error en comparación de fricción: {e}")

def plot_reversion_baja_velocidad():
    try:
        df = pd.read_csv("experiments/f1_4_low_speed_reversal_friction.csv")
        plt.figure()
        plt.plot(df['t'], df['omega_base'], 'b-', linewidth=1.5, label='Sin fricción')
        plt.plot(df['t'], df['omega_friction'], 'r-', linewidth=1.5, label='Con fricción (Base)')
        plt.plot(df['t'], df['omega_ref'], 'k--', linewidth=1.2, label='Referencia $\omega_m^*$')
        
        plt.xlabel('Tiempo [s]')
        plt.ylabel('Velocidad $\omega_m$ [rad/s]')
        plt.title('Respuesta a baja velocidad y reversión con fricción (F1.4)')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        guardar_figura("fig_f1_4_reversion_baja_velocidad")
        print("✅ Gráfica de reversión a baja velocidad generada.")
    except Exception as e:
        print(f"⚠️ Error en reversión: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando generación de gráficas para la tesis...\n")
    plot_friccion()
    plot_seguimiento_corriente()
    plot_velocidad_con_carga()
    plot_comparacion_friccion()
    plot_reversion_baja_velocidad()
    print(f"\n🎉 ¡Listo! Las gráficas se guardaron en la carpeta: ./{OUTPUT_DIR}/")

def plot_frontera_pareto_b25():
    try:
        # Usamos el resumen del barrido (ajusta el nombre si tu CSV se llama diferente)
        df = pd.read_csv("experiments/b2_5a_pi_sweep_summary.csv")
        
        plt.figure(figsize=(9, 6))
        
        # Filtrar configuraciones admisibles (< 79.5 A) y no admisibles
        admisibles = df[df['max_iq'] <= 79.5]
        no_admisibles = df[df['max_iq'] > 79.5]
        
        # Gráfica de dispersión
        plt.scatter(no_admisibles['max_iq'], no_admisibles['mae'], 
                    color='red', alpha=0.5, label='No admisibles (> 79.5 A)', zorder=1)
        plt.scatter(admisibles['max_iq'], admisibles['mae'], 
                    color='green', alpha=0.8, label='Admisibles (≤ 79.5 A)', zorder=2)
        
        # Línea de restricción
        plt.axvline(x=79.5, color='black', linestyle='--', linewidth=1.5, 
                    label='Límite de corriente (79.5 A)')
        
        # Resaltar las 3 configuraciones candidatas (A, B, C) si existen en el CSV
        # (Ajusta los valores de mae y max_iq según tus resultados reales de la tabla)
        # plt.scatter([52.8, 52.8, 79.2], [0.78, 0.65, 0.52], color='blue', marker='X', s=100, label='Candidatas A, B, C', zorder=3)
        
        plt.xlabel('Demanda máxima de corriente $|i_q^*|_{max}$ [A]')
        plt.ylabel('Error Absoluto Medio (MAE) [rad/s]')
        plt.title('Frontera de compromiso: Seguimiento vs. Esfuerzo de control (B2.5)')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend(loc='upper right')
        
        # Invertir eje Y si quieres que "mejor" sea arriba a la izquierda, 
        # pero en MAE "mejor" es abajo a la izquierda, así que lo dejamos normal.
        plt.xlim(40, 120)
        
        guardar_figura("fig_b2_5_frontera_pareto")
        print("✅ Gráfica de Frontera de Pareto (B2.5) generada.")
    except Exception as e:
        print(f"⚠️ Error en Frontera de Pareto: {e}")

def plot_evolucion_ganancias_anfis():
    # Esta gráfica requiere que ya tengas un CSV de una simulación con ANFIS corriendo.
    # La dejaremos lista para cuando tengas el archivo 'anfis_simulation_results.csv'
    try:
        df = pd.read_csv("experiments/anfis_simulation_results.csv")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        
        ax1.plot(df['t'], df['omega_m'], 'b-', linewidth=1.5, label='$\omega_m$ real')
        ax1.plot(df['t'], df['omega_ref'], 'k--', linewidth=1.2, label='Referencia')
        ax1.set_ylabel(r'Velocidad [rad/s]')
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle=':', alpha=0.7)
        
        ax2.plot(df['t'], df['kp_adapt'], 'r-', linewidth=1.5, label='$K_p^{adapt}$')
        ax2.plot(df['t'], df['ki_adapt'], 'g-', linewidth=1.5, label='$K_i^{adapt}$')
        ax2.set_xlabel('Tiempo [s]')
        ax2.set_ylabel('Ganancias del PI')
        ax2.legend(loc='upper right')
        ax2.grid(True, linestyle=':', alpha=0.7)
        
        plt.suptitle('Evolución temporal de la adaptación de ganancias (ANFIS)')
        guardar_figura("fig_anfis_evolucion_ganancias")
        print("✅ Gráfica de evolución de ganancias ANFIS generada.")
    except FileNotFoundError:
        print("⏳ Gráfica de ganancias ANFIS omitida (falta el CSV de simulación ANFIS).")

# Agregar al bloque principal
if __name__ == "__main__":
    print("🚀 Generando gráficas adicionales para la tesis...\n")
    plot_frontera_pareto_b25()
    plot_evolucion_ganancias_anfis()
