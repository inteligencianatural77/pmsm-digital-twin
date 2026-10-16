"""
J3.3 — Prototipo de evaluación condicionada al estado.

OBJETIVO
--------
Comprobar que una trayectoria B2.5/J1 puede capturarse y restaurarse
incluyendo los estados internos relevantes de:

    - PMSM
    - PI de velocidad
    - PI de corriente d/q

El prototipo NO genera todavía el dataset completo de etiquetas ANFIS.

La finalidad de esta etapa es validar experimentalmente la intervención:

    estado x_k
        -> candidato A
        -> candidato B
        -> comparación desde el mismo estado inicial

IMPORTANTE
----------
El vector z=[error, delta_error, abs_iq] NO se amplía aquí.

El estado completo se utiliza únicamente para generar etiquetas
contrafactuales de forma reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.foc.speed_controller import SpeedController
from pmsm_hybrid_control.plant.friction import (
    StribeckFriction,
    StribeckFrictionParameters,
)
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.plant.pmsm_with_friction import PMSMWithFriction


DT = 50e-6
WINDOW = 0.010

ID_REF = 0.0
T_LOAD = 0.0

KP_BASE = 5.2804
KI_BASE = 1.2693

OUTPUT_DIR = Path("experiments/j3_3_state_conditioned")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROBE_FILE = OUTPUT_DIR / "j3_3_probe.csv"


@dataclass(frozen=True)
class Scenario:
    name: str
    tc: float
    ts: float
    omega_s: float
    delta: float
    b: float


@dataclass(frozen=True)
class FullState:
    """Estado necesario para reiniciar una intervención."""

    id: float
    iq: float
    omega_m: float
    theta_m: float

    int_w: float
    iq_ref_state: float

    int_id: float
    int_iq: float


def build_plant(scenario: Scenario):
    if scenario.name == "no_friction":
        return PMSMBase()

    friction = StribeckFriction(
        StribeckFrictionParameters(
            tc=scenario.tc,
            ts=scenario.ts,
            omega_s=scenario.omega_s,
            delta=scenario.delta,
            b=scenario.b,
        )
    )

    return PMSMWithFriction(friction=friction)


def build_controllers(plant, kp: float, ki: float):
    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
    )

    speed_controller = SpeedController(
        kp_w=kp,
        ki_w=ki,
    )

    return foc, speed_controller


def capture_state(plant, speed_controller, foc) -> FullState:
    """Captura todos los estados internos relevantes."""

    return FullState(
        id=float(plant._id),
        iq=float(plant._iq),
        omega_m=float(plant._omega_m),
        theta_m=float(plant._theta_m),
        int_w=float(speed_controller.int_w),
        iq_ref_state=float(speed_controller.iq_ref_state),
        int_id=float(foc.current_controller.int_id),
        int_iq=float(foc.current_controller.int_iq),
    )


def restore_state(
    plant,
    speed_controller,
    foc,
    state: FullState,
) -> None:
    """Restaura exactamente el estado capturado."""

    plant._id = float(state.id)
    plant._iq = float(state.iq)
    plant._omega_m = float(state.omega_m)
    plant._theta_m = float(state.theta_m)

    speed_controller.int_w = float(state.int_w)
    speed_controller.iq_ref_state = float(state.iq_ref_state)

    foc.current_controller.int_id = float(state.int_id)
    foc.current_controller.int_iq = float(state.int_iq)


def make_output(plant, speed_controller, foc) -> dict[str, float]:
    """Extrae el estado restaurado para verificar igualdad."""

    return {
        "plant_id": float(plant._id),
        "plant_iq": float(plant._iq),
        "omega_m": float(plant._omega_m),
        "theta_m": float(plant._theta_m),
        "int_w": float(speed_controller.int_w),
        "iq_ref_state": float(speed_controller.iq_ref_state),
        "int_id": float(foc.current_controller.int_id),
        "int_iq": float(foc.current_controller.int_iq),
    }


def run_one_step(
    plant,
    foc,
    speed_controller,
    omega_ref: float,
):
    """Ejecuta un único paso del lazo completo."""

    output = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=T_LOAD,
        ),
        dt=DT,
    )

    error = omega_ref - output.omega_m

    iq_ref = speed_controller.update(
        omega_ref=omega_ref,
        omega_meas=output.omega_m,
        dt=DT,
    )

    va, vb, vc = foc.step(
        ia=output.ia,
        ib=output.ib,
        ic=output.ic,
        theta_m=output.theta_m,
        omega_m=output.omega_m,
        id_ref=ID_REF,
        iq_ref=iq_ref,
        dt=DT,
    )

    output = plant.step(
        PlantInput(
            va=va,
            vb=vb,
            vc=vc,
            t_load=T_LOAD,
        ),
        dt=DT,
    )

    tf = 0.0
    if hasattr(plant, "friction_torque"):
        tf = plant.friction_torque()

    return {
        "omega_m": float(output.omega_m),
        "error": float(error),
        "iq_ref": float(iq_ref),
        "iq": float(output.iq),
        "te": float(output.te),
        "tf": float(tf),
    }


def main() -> None:
    scenario = Scenario(
        name="friction_base",
        tc=0.5,
        ts=0.8,
        omega_s=10.0,
        delta=2.0,
        b=0.01,
    )

    # Estado inicial común.
    reference_plant = build_plant(scenario)
    reference_foc, reference_speed = build_controllers(
        reference_plant,
        KP_BASE,
        KI_BASE,
    )

    # Avanzamos deliberadamente algunos pasos para obtener un estado
    # no trivial que contenga memoria de todos los controladores.
    for _ in range(20):
        run_one_step(
            reference_plant,
            reference_foc,
            reference_speed,
            omega_ref=20.0,
        )

    state = capture_state(
        reference_plant,
        reference_speed,
        reference_foc,
    )

    print("=" * 60)
    print("J3.3 — STATE-CONDITIONED PROBE")
    print("=" * 60)
    print()
    print("Estado de intervención:")
    print(f"  id       = {state.id:.12f}")
    print(f"  iq       = {state.iq:.12f}")
    print(f"  omega_m  = {state.omega_m:.12f}")
    print(f"  theta_m  = {state.theta_m:.12f}")
    print(f"  int_w    = {state.int_w:.12f}")
    print(f"  iq_ref   = {state.iq_ref_state:.12f}")
    print(f"  int_id   = {state.int_id:.12f}")
    print(f"  int_iq   = {state.int_iq:.12f}")
    print()

    candidates = [
        ("A", 0.50, 0.50),
        ("C", 0.75, 2.00),
    ]

    rows = []

    for candidate_name, kp_factor, ki_factor in candidates:
        kp = KP_BASE * kp_factor
        ki = KI_BASE * ki_factor

        plant = build_plant(scenario)
        foc, speed_controller = build_controllers(
            plant,
            kp,
            ki,
        )

        restore_state(
            plant,
            speed_controller,
            foc,
            state,
        )

        restored = make_output(
            plant,
            speed_controller,
            foc,
        )

        max_abs_error = 0.0
        sum_abs_error = 0.0
        max_abs_iq = 0.0
        samples = 0

        steps = int(round(WINDOW / DT))

        for _ in range(steps):
            result = run_one_step(
                plant,
                foc,
                speed_controller,
                omega_ref=20.0,
            )

            abs_error = abs(result["error"])
            abs_iq = abs(result["iq"])

            sum_abs_error += abs_error
            max_abs_error = max(max_abs_error, abs_error)
            max_abs_iq = max(max_abs_iq, abs_iq)
            samples += 1

        mae = sum_abs_error / samples

        rows.append(
            {
                "candidate": candidate_name,
                "kp_factor": kp_factor,
                "ki_factor": ki_factor,
                "kp": kp,
                "ki": ki,
                "initial_id": state.id,
                "initial_iq": state.iq,
                "initial_omega_m": state.omega_m,
                "initial_theta_m": state.theta_m,
                "initial_int_w": state.int_w,
                "initial_int_id": state.int_id,
                "initial_int_iq": state.int_iq,
                "restored_id": restored["plant_id"],
                "restored_iq": restored["plant_iq"],
                "restored_omega_m": restored["omega_m"],
                "restored_theta_m": restored["theta_m"],
                "restored_int_w": restored["int_w"],
                "restored_int_id": restored["int_id"],
                "restored_int_iq": restored["int_iq"],
                "window_s": WINDOW,
                "samples": samples,
                "mae": mae,
                "max_abs_error": max_abs_error,
                "max_abs_iq": max_abs_iq,
            }
        )

    with PROBE_FILE.open("w", encoding="utf-8") as f:
        headers = list(rows[0].keys())
        f.write(",".join(headers) + "\n")

        for row in rows:
            f.write(
                ",".join(
                    str(row[h])
                    for h in headers
                )
                + "\n"
            )

    print("Resultados:")
    for row in rows:
        print(
            f"  {row['candidate']}: "
            f"MAE={row['mae']:.9f}, "
            f"max|e|={row['max_abs_error']:.9f}, "
            f"max|iq|={row['max_abs_iq']:.9f}"
        )

    print()
    print(f"CSV: {PROBE_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
