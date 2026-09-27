"""Punto de entrada — Phase 0 + Phase 1 (+ avance Phase 2 MAPAS por instruccion explicita del usuario).
Ejecuta la prueba de consistencia de software y el reporte de fase."""
from pmsm_hybrid_control.plant.parameters import default_m4_parameters, LAMBDA_M, B_PENDING, TFRIC_PENDING
from pmsm_hybrid_control.simulation.run_simulation import run_open_loop_test


def main() -> None:
    params = default_m4_parameters()
    print("=== pmsm_hybrid_control — M4_BASE (consistencia de software) ===")
    print(f"Rs={params.rs} ohm | Ld={params.ld} H | Lq={params.lq} H | "
          f"lambda_m={LAMBDA_M.value} Wb (M4, NO CloudE 0.11) | p={params.n_pole_pairs} | J={params.j}")
    print(f"PENDING (no inventados): B={B_PENDING.status.value}, Tfric={TFRIC_PENDING.status.value}")

    traj = run_open_loop_test(duration_s=0.02, dt=50e-6)
    last = traj[-1]
    print(f"Pasos: {len(traj)} | ia={last.ia:.4f} A | iq={last.iq:.4f} A | "
          f"omega_m={last.omega_m:.4f} rad/s | Te={last.te:.4f} N*m")
    print("NOTA: prueba de CONSISTENCIA DE SOFTWARE, no validacion fisica.")


if __name__ == "__main__":
    main()
