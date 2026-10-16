import numpy as np
import matplotlib.pyplot as plt
import os

plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "figure.figsize": (9, 6)
})

OUTPUT_DIR = "graficas_tesis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Funciones de pertenencia personalizadas para robustez en fronteras
def z_shape(x, a, b):
    """Función en forma de Z (para 'Negativo' o 'Baja')"""
    y = np.ones_like(x)
    y[x > a] = 1 - (x[x > a] - a) / (b - a)
    y[x >= b] = 0
    return np.clip(y, 0, 1)

def s_shape(x, a, b):
    """Función en forma de S (para 'Positivo' o 'Alta')"""
    y = np.zeros_like(x)
    y[x < a] = 0
    y[(x >= a) & (x <= b)] = (x[(x >= a) & (x <= b)] - a) / (b - a)
    y[x > b] = 1
    return np.clip(y, 0, 1)

def gaussian(x, mu, sigma):
    """Función Gaussiana (para 'Cero' o 'Media')"""
    return np.exp(-0.5 * ((x - mu) / sigma)**2)

def guardar_figura(nombre):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.pdf"), format='pdf', bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f"{nombre}.png"), format='png', bbox_inches='tight')
    plt.close()

# ==============================================================================
# 1. Funciones de Membresía para el Error de Velocidad (e_omega)
# Universo: [-50, 50] rad/s
# ==============================================================================
x_e = np.linspace(-60, 60, 500)
plt.figure()
plt.plot(x_e, z_shape(x_e, -50, -15), 'b-', linewidth=2, label=r'Negativo (Z-shape)')
plt.plot(x_e, gaussian(x_e, 0, 15), 'g-', linewidth=2, label=r'Cero (Gaussiana)')
plt.plot(x_e, s_shape(x_e, 15, 50), 'r-', linewidth=2, label=r'Positivo (S-shape)')

plt.xlabel(r'Error de velocidad $e_\omega$ [rad/s]')
plt.ylabel(r'Grado de pertenencia $\mu$')
plt.title('Funciones de membresía para el error de velocidad ($e_\omega$)')
plt.axvline(0, color='black', linestyle=':', alpha=0.5)
plt.axvline(-50, color='gray', linestyle='--', alpha=0.5, label='Límite universo (-50)')
plt.axvline(50, color='gray', linestyle='--', alpha=0.5, label='Límite universo (50)')
plt.ylim(0, 1.1)
plt.xlim(-60, 60)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')
guardar_figura("fig_anfis_mf_error_velocidad")
print("✅ Gráfica MF Error de Velocidad generada.")

# ==============================================================================
# 2. Funciones de Membresía para la Variación del Error (Delta_e_omega)
# Universo: [-20, 20] rad/s²
# ==============================================================================
x_de = np.linspace(-30, 30, 500)
plt.figure()
plt.plot(x_de, z_shape(x_de, -20, -5), 'b-', linewidth=2, label=r'Negativo (Z-shape)')
plt.plot(x_de, gaussian(x_de, 0, 5), 'g-', linewidth=2, label=r'Cero (Gaussiana)')
plt.plot(x_de, s_shape(x_de, 5, 20), 'r-', linewidth=2, label=r'Positivo (S-shape)')

plt.xlabel(r'Variación del error $\Delta e_\omega$ [rad/s$^2$]')
plt.ylabel(r'Grado de pertenencia $\mu$')
plt.title(r'Funciones de membresía para la variación del error ($\Delta e_\omega$)')
plt.axvline(0, color='black', linestyle=':', alpha=0.5)
plt.ylim(0, 1.1)
plt.xlim(-30, 30)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')
guardar_figura("fig_anfis_mf_delta_error")
print("✅ Gráfica MF Variación del Error generada.")

# ==============================================================================
# 3. Funciones de Membresía para la Magnitud de Corriente (|i_q|)
# Universo: [0, 120] A
# ==============================================================================
x_iq = np.linspace(-10, 130, 500)
plt.figure()
plt.plot(x_iq, z_shape(x_iq, 0, 30), 'b-', linewidth=2, label=r'Baja (Z-shape)')
plt.plot(x_iq, gaussian(x_iq, 60, 20), 'g-', linewidth=2, label=r'Media (Gaussiana)')
plt.plot(x_iq, s_shape(x_iq, 90, 120), 'r-', linewidth=2, label=r'Alta (S-shape)')

plt.xlabel(r'Magnitud de corriente $|i_q|$ [A]')
plt.ylabel(r'Grado de pertenencia $\mu$')
plt.title(r'Funciones de membresía para la magnitud de corriente ($|i_q|$)')
plt.axvline(79.5, color='red', linestyle='-.', linewidth=1.5, label='Límite admisible (79.5 A)')
plt.ylim(0, 1.1)
plt.xlim(-10, 130)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')
guardar_figura("fig_anfis_mf_corriente")
print("✅ Gráfica MF Corriente generada.")

print(f"\n🎉 ¡Listo! Gráficas de funciones de membresía guardadas en: ./{OUTPUT_DIR}/")
