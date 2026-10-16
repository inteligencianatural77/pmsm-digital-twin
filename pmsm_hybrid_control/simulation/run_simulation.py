"""CORRIDA DE SIMULACION — PHASE 1 incluye solo prueba de consistencia.

Simulacion formal con escenarios y validacion: PHASE 6.
ESTADO: parcial (consistencia de software)."""
from __future__ import annotations

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput


def run_open_loop_test(duration_s: float = 0.05, dt: float = 50e-6) -> list:
    """Prueba de consistencia de software (NO validacion fisica).

    Aplica tension de fase balanceada de baja amplitud y devuelve la
    trayectoria de salidas. Uso de dt = 50e-6 es una eleccion numerica
    interna PROPOSED; NO se afirma que sea la frecuencia de muestreo del
    sistema (Ts CloudE = 50 us es solo referencia).
    """
    plant = PMSMBase()
    steps = int(duration_s / dt)
    trajectory = []
    import math
    for k in range(steps):
        t = k * dt
        # Tension abc balanceada pequena (condicion de prueba, no de operacion)
        va = 5.0 * math.sin(2 * math.pi * 50.0 * t)
        vb = 5.0 * math.sin(2 * math.pi * 50.0 * t - 2 * math.pi / 3)
        vc = 5.0 * math.sin(2 * math.pi * 50.0 * t + 2 * math.pi / 3)
        out = plant.step(
            PlantInput(va=va, vb=vb, vc=vc, t_load=0.0),
            dt,
        )
        trajectory.append(out)
    return trajectory


if __name__ == "__main__":
    trajectory = run_open_loop_test()
    final = trajectory[-1]

    print("===== PRUEBA DE CONSISTENCIA PMSM =====")
    print(f"Muestras: {len(trajectory)}")
    print(f"Duración: {len(trajectory) * 50e-6:.6f} s")
    print(f"id final: {final.id:.6f} A")
    print(f"iq final: {final.iq:.6f} A")
    print(f"omega_m final: {final.omega_m:.6f} rad/s")
    print(f"theta_m final: {final.theta_m:.6f} rad")
    print(f"Te final: {final.te:.6f} N·m")
