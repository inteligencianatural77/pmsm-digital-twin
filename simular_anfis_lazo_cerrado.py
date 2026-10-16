import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 12,
    "font.size": 11,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "figure.figsize": (10, 6)
})

OUTPUT_DIR = "graficas_tesis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Parámetros del motor Siemens 1FT7087
Rs = 0.05
Ld = 0.0012
Lq = 0.0012
lambda_m = 0.107245
J = 0.00416
p = 4

# Parámetros del controlador PI (baseline)
Kp0 = 5.2804
Ki0 = 1.2693

# Parámetros de fricción (escenario base)
Tc = 0.50
Ts = 0.80
omega_s = 10
delta = 2
B = 0.010

# ============================================================================
# MODELO DEL PMSM
# ============================================================================
def friction_model(omega_m):
    """Modelo de fricción no lineal (Stribeck)"""
    if abs(omega_m) < 1e-6:
        return 0.0
    
    sign_omega = np.sign(omega_m)
    abs_omega = abs(omega_m)
    
    T_f = (Tc + (Ts - Tc) * np.exp(-(abs_omega / omega_s)**delta)) * sign_omega + B * omega_m
    return T_f

def pmsm_dynamics(t, state, vd, vq, T_load):
    """Dinámica del PMSM en coordenadas dq"""
    id, iq, omega_m, theta_m = state
    
    # Velocidad eléctrica
    omega_e = p * omega_m
    
    # Ecuaciones eléctricas
    did_dt = (vd - Rs * id + omega_e * Lq * iq) / Ld
    diq_dt = (vq - Rs * iq - omega_e * (Ld * id + lambda_m)) / Lq
    
    # Par electromagnético
    Te = 1.5 * p * lambda_m * iq
    
    # Fricción
    T_f = friction_model(omega_m)
    
    # Ecuación mecánica
    domega_dt = (Te - T_load - T_f) / J
    
    # Posición
    dtheta_dt = omega_m
    
    return [did_dt, diq_dt, domega_dt, dtheta_dt]

# ============================================================================
# CONTROLADOR FOC+PI
# ============================================================================
def pi_controller(error, Kp, Ki, integral_state, dt):
    """Controlador PI con anti-windup"""
    integral_state += error * dt
    output = Kp * error + Ki * integral_state
    return output, integral_state

# ============================================================================
# ANFIS SUPERVISOR (Basado en reglas expertas)
# ============================================================================
def z_shape(x, a, b):
    """Función Z-shape para 'Negativo' o 'Baja'"""
    if x <= a:
        return 1.0
    elif x >= b:
        return 0.0
    else:
        return 1.0 - (x - a) / (b - a)

def s_shape(x, a, b):
    """Función S-shape para 'Positivo' o 'Alta'"""
    if x <= a:
        return 0.0
    elif x >= b:
        return 1.0
    else:
        return (x - a) / (b - a)

def gaussian(x, mu, sigma):
    """Función Gaussiana para 'Cero' o 'Media'"""
    return np.exp(-0.5 * ((x - mu) / sigma)**2)

def anfis_supervisor(e_omega, delta_e_omega, iq_abs):
    """
    ANFIS supervisor basado en reglas expertas.
    Retorna factores de adaptación alpha_p y alpha_i.
    """
    # ========================================================================
    # FUZZIFICACIÓN
    # ========================================================================
    # Error de velocidad (universo: -50 a 50 rad/s)
    mu_e_neg = z_shape(e_omega, -50, -15)
    mu_e_zero = gaussian(e_omega, 0, 15)
    mu_e_pos = s_shape(e_omega, 15, 50)
    
    # Variación del error (universo: -20 a 20 rad/s²)
    mu_de_neg = z_shape(delta_e_omega, -20, -5)
    mu_de_zero = gaussian(delta_e_omega, 0, 5)
    mu_de_pos = s_shape(delta_e_omega, 5, 20)
    
    # Corriente (universo: 0 a 120 A)
    mu_iq_low = z_shape(iq_abs, 0, 30)
    mu_iq_med = gaussian(iq_abs, 60, 20)
    mu_iq_high = s_shape(iq_abs, 90, 120)
    
    # ========================================================================
    # REGLAS EXPERTAS (simplificadas a 9 reglas clave)
    # ========================================================================
    # Regla 1: Error grande positivo + corriente baja → Aumentar Kp mucho
    w1 = mu_e_pos * mu_iq_low
    alpha_p1 = 1.8
    alpha_i1 = 1.2
    
    # Regla 2: Error grande positivo + corriente alta → Aumentar Kp moderado
    w2 = mu_e_pos * mu_iq_high
    alpha_p2 = 1.3
    alpha_i2 = 1.0
    
    # Regla 3: Error cercano a cero + corriente media → Mantener nominal
    w3 = mu_e_zero * mu_iq_med
    alpha_p3 = 1.0
    alpha_i3 = 1.0
    
    # Regla 4: Error grande negativo + corriente baja → Reducir Kp (evitar sobreimpulso)
    w4 = mu_e_neg * mu_iq_low
    alpha_p4 = 0.7
    alpha_i4 = 0.8
    
    # Regla 5: Error grande negativo + corriente alta → Reducir Kp mucho
    w5 = mu_e_neg * mu_iq_high
    alpha_p5 = 0.5
    alpha_i5 = 0.6
    
    # Regla 6: Error creciendo + corriente baja → Aumentar Kp
    w6 = mu_de_pos * mu_iq_low
    alpha_p6 = 1.5
    alpha_i6 = 1.1
    
    # Regla 7: Error decreciendo + corriente media → Mantener
    w7 = mu_de_neg * mu_iq_med
    alpha_p7 = 0.9
    alpha_i7 = 0.9
    
    # Regla 8: Error cero + corriente baja → Conservador
    w8 = mu_e_zero * mu_iq_low
    alpha_p8 = 0.8
    alpha_i8 = 0.7
    
    # Regla 9: Error cero + corriente alta → Conservador
    w9 = mu_e_zero * mu_iq_high
    alpha_p9 = 0.6
    alpha_i9 = 0.5
    
    # ========================================================================
    # DEFUZZIFICACIÓN (promedio ponderado)
    # ========================================================================
    weights = np.array([w1, w2, w3, w4, w5, w6, w7, w8, w9])
    alpha_p_values = np.array([alpha_p1, alpha_p2, alpha_p3, alpha_p4, alpha_p5, 
                                alpha_p6, alpha_p7, alpha_p8, alpha_p9])
    alpha_i_values = np.array([alpha_i1, alpha_i2, alpha_i3, alpha_i4, alpha_i5,
                                alpha_i6, alpha_i7, alpha_i8, alpha_i9])
    
    total_weight = np.sum(weights)
    if total_weight < 1e-6:
        return 1.0, 1.0  # Si no hay activación, mantener nominal
    
    alpha_p = np.sum(weights * alpha_p_values) / total_weight
    alpha_i = np.sum(weights * alpha_i_values) / total_weight
    
    # Limitar a rangos seguros
    alpha_p = np.clip(alpha_p, 0.5, 2.0)
    alpha_i = np.clip(alpha_i, 0.5, 1.5)
    
    return alpha_p, alpha_i

# ============================================================================
# SIMULACIÓN EN LAZO CERRADO
# ============================================================================
def simulate_closed_loop(use_anfis=False, duration=0.5, dt=50e-6):
    """Simula el sistema en lazo cerrado con PI fijo o ANFIS"""
    
    # Perfil de referencia (reversión a baja velocidad)
    def omega_ref(t):
        if t < 0.05:
            return 0.0
        elif t < 0.15:
            return 20.0
        elif t < 0.25:
            return 0.0
        elif t < 0.35:
            return -20.0
        else:
            return 0.0
    
    # Estado inicial
    state = [0.0, 0.0, 0.0, 0.0]  # id, iq, omega_m, theta_m
    
    # Estados del controlador
    integral_id = 0.0
    integral_iq = 0.0
    integral_omega = 0.0
    
    # Historial
    t_hist = []
    omega_m_hist = []
    omega_ref_hist = []
    iq_ref_hist = []
    iq_hist = []
    Te_hist = []
    Kp_hist = []
    Ki_hist = []
    
    t = 0.0
    e_omega_prev = 0.0
    
    while t < duration:
        # Referencia de velocidad
        omega_ref_t = omega_ref(t)
        
        # Error de velocidad
        e_omega = omega_ref_t - state[2]
        delta_e_omega = (e_omega - e_omega_prev) / dt
        
        # Corriente absoluta
        iq_abs = abs(state[1])
        
        # Determinar ganancias
        if use_anfis:
            alpha_p, alpha_i = anfis_supervisor(e_omega, delta_e_omega, iq_abs)
            Kp = Kp0 * alpha_p
            Ki = Ki0 * alpha_i
        else:
            Kp = Kp0
            Ki = Ki0
            alpha_p = 1.0
            alpha_i = 1.0
        
        # Lazo de velocidad
        iq_ref_raw, integral_omega = pi_controller(e_omega, Kp, Ki, integral_omega, dt)
        iq_ref = np.clip(iq_ref_raw, -112.43, 112.43)
        
        # Lazo de corriente (id)
        id_ref = 0.0
        error_id = id_ref - state[0]
        vd_pi, integral_id = pi_controller(error_id, 15.0796, 628.3185, integral_id, dt)
        vd_dec = -p * state[2] * Lq * state[1]
        vd = vd_pi + vd_dec
        vd = np.clip(vd, -200, 200)
        
        # Lazo de corriente (iq)
        error_iq = iq_ref - state[1]
        vq_pi, integral_iq = pi_controller(error_iq, 15.0796, 628.3185, integral_iq, dt)
        vq_dec = p * state[2] * (Ld * state[0] + lambda_m)
        vq = vq_pi + vq_dec
        vq = np.clip(vq, -200, 200)
        
        # Par electromagnético
        Te = 1.5 * p * lambda_m * state[1]
        
        # Guardar historial
        t_hist.append(t)
        omega_m_hist.append(state[2])
        omega_ref_hist.append(omega_ref_t)
        iq_ref_hist.append(iq_ref)
        iq_hist.append(state[1])
        Te_hist.append(Te)
        Kp_hist.append(Kp)
        Ki_hist.append(Ki)
        
        # Integrar dinámica
        sol = solve_ivp(pmsm_dynamics, [t, t + dt], state, args=(vd, vq, 0.0), 
                       method='RK45', max_step=dt)
        state = sol.y[:, -1]
        
        e_omega_prev = e_omega
        t += dt
    
    return {
        't': t_hist,
        'omega_m': omega_m_hist,
        'omega_ref': omega_ref_hist,
        'iq_ref': iq_ref_hist,
        'iq': iq_hist,
        'Te': Te_hist,
        'Kp': Kp_hist,
        'Ki': Ki_hist
    }

# ============================================================================
# EJECUTAR SIMULACIONES
# ============================================================================
print("🚀 Simulando FOC+PI fijo...")
results_pi = simulate_closed_loop(use_anfis=False, duration=0.5)
print("✅ Simulación PI completada.")

print("🚀 Simulando FOC+PI+ANFIS...")
results_anfis = simulate_closed_loop(use_anfis=True, duration=0.5)
print("✅ Simulación ANFIS completada.")

# ============================================================================
# GUARDAR RESULTADOS EN CSV
# ============================================================================
df_pi = pd.DataFrame(results_pi)
df_pi.to_csv("experiments/sim_pi_fixed.csv", index=False)
print("✅ Resultados PI guardados: experiments/sim_pi_fixed.csv")

df_anfis = pd.DataFrame(results_anfis)
df_anfis.to_csv("experiments/sim_anfis_adaptive.csv", index=False)
print("✅ Resultados ANFIS guardados: experiments/sim_anfis_adaptive.csv")

# ============================================================================
# GRÁFICA 1: COMPARACIÓN DIRECTA
# ============================================================================
plt.figure(figsize=(10, 6))
plt.plot(results_pi['t'], results_pi['omega_m'], 'b--', linewidth=1.5, label='FOC+PI (fijo)')
plt.plot(results_anfis['t'], results_anfis['omega_m'], 'r-', linewidth=1.5, label='FOC+PI+ANFIS (adaptativo)')
plt.plot(results_pi['t'], results_pi['omega_ref'], 'k:', linewidth=1.2, label='Referencia $\omega_m^*$')

plt.xlabel('Tiempo [s]')
plt.ylabel(r'Velocidad $\omega_m$ [rad/s]')
plt.title('Comparación de respuesta de velocidad: FOC+PI vs. FOC+PI+ANFIS')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "fig_comparacion_pi_vs_anfis.pdf"), format='pdf', bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, "fig_comparacion_pi_vs_anfis.png"), format='png', bbox_inches='tight')
print("✅ Gráfica de comparación generada.")

# ============================================================================
# GRÁFICA 2: EVOLUCIÓN DE GANANCIAS
# ============================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Subgráfica 1: Velocidad
ax1.plot(results_anfis['t'], results_anfis['omega_m'], 'b-', linewidth=1.5, label=r'$\omega_m$ real')
ax1.plot(results_anfis['t'], results_anfis['omega_ref'], 'k--', linewidth=1.2, label=r'Referencia $\omega_m^*$')
ax1.set_ylabel(r'Velocidad [rad/s]')
ax1.legend(loc='upper right')
ax1.grid(True, linestyle=':', alpha=0.7)
ax1.set_title('Evolución temporal con ANFIS adaptativo')

# Subgráfica 2: Ganancias
ax2.plot(results_anfis['t'], results_anfis['Kp'], 'r-', linewidth=1.5, label=r'$K_p^{adapt}$')
ax2.plot(results_anfis['t'], results_anfis['Ki'], 'g-', linewidth=1.5, label=r'$K_i^{adapt}$')
ax2.axhline(Kp0, color='red', linestyle=':', alpha=0.5, label=r'$K_{p0}$ (nominal)')
ax2.axhline(Ki0, color='green', linestyle=':', alpha=0.5, label=r'$K_{i0}$ (nominal)')
ax2.set_xlabel('Tiempo [s]')
ax2.set_ylabel('Ganancias del PI')
ax2.legend(loc='upper right')
ax2.grid(True, linestyle=':', alpha=0.7)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "fig_anfis_evolucion_ganancias.pdf"), format='pdf', bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, "fig_anfis_evolucion_ganancias.png"), format='png', bbox_inches='tight')
print("✅ Gráfica de evolución de ganancias generada.")

print(f"\n🎉 ¡Listo! Todas las gráficas guardadas en: ./{OUTPUT_DIR}/")
