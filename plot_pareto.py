import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "figure.figsize": (9, 6)
})

df = pd.read_csv("experiments/b2_5_parameter_sweep_metrics.csv")

# Agrupar por configuración (kp_factor, ki_factor) para obtener el MAE promedio y el max_iq peor caso
grouped = df.groupby(['kp_factor', 'ki_factor']).agg(
    mae_avg=('mae_rad_s', 'mean'),
    max_iq=('iq_ref_max_A', 'max'),
    final_error_avg=('final_abs_error_rad_s', 'mean')
).reset_index()

plt.figure()

# Filtrar admisibles vs no admisibles (límite 79.5 A)
admisibles = grouped[grouped['max_iq'] <= 79.5]
no_admisibles = grouped[grouped['max_iq'] > 79.5]

plt.scatter(no_admisibles['max_iq'], no_admisibles['mae_avg'], 
            color='red', alpha=0.4, s=60, label='No admisibles (> 79.5 A)', zorder=1, edgecolors='darkred')
plt.scatter(admisibles['max_iq'], admisibles['mae_avg'], 
            color='green', alpha=0.7, s=70, label='Admisibles (≤ 79.5 A)', zorder=2, edgecolors='darkgreen')

# Línea de restricción
plt.axvline(x=79.5, color='black', linestyle='--', linewidth=1.5, 
            label='Límite documentado (79.5 A)')

# Identificar las 3 candidatas A, B, C (factores 0.50/0.50, 0.50/2.00, 0.75/2.00)
candidatas = grouped[
    ((grouped['kp_factor'] == 0.50) & (grouped['ki_factor'] == 0.50)) |
    ((grouped['kp_factor'] == 0.50) & (grouped['ki_factor'] == 2.00)) |
    ((grouped['kp_factor'] == 0.75) & (grouped['ki_factor'] == 2.00))
]

if len(candidatas) > 0:
    plt.scatter(candidatas['max_iq'], candidatas['mae_avg'], 
                color='blue', marker='*', s=250, label='Candidatas A, B, C', zorder=3, edgecolors='black', linewidths=0.8)

plt.xlabel(r'Demanda máxima de corriente $|i_q^*|_{\max}$ [A]')
plt.ylabel('Error Absoluto Medio (MAE) [rad/s]')
plt.title('Frontera de Pareto del barrido B2.5: Compromiso Seguimiento vs. Esfuerzo de Control')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')
plt.tight_layout()

plt.savefig("graficas_tesis/fig_b2_5_frontera_pareto.pdf", format='pdf', bbox_inches='tight')
plt.savefig("graficas_tesis/fig_b2_5_frontera_pareto.png", format='png', bbox_inches='tight')
print("✅ Frontera de Pareto generada: graficas_tesis/fig_b2_5_frontera_pareto.pdf")
