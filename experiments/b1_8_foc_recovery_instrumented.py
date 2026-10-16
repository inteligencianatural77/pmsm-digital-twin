"""B1.8 — Recuperación de iq al retirar una referencia alta.

Instrumentación temporal de una instancia del FOC activo.
No modifica módulos de producción.
VDC=540 V es provisional y la referencia alta es una condición de estrés.
"""

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from pmsm_hybrid_control.foc.foc import FOC
from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.transforms.clarke import clarke_transform
from pmsm_hybrid_control.transforms.park import (
    mechanical_to_electrical_angle,
    park_transform,
)

DT = 50e-6
T_END = 0.050
T_RELEASE = 0.025
VDC_PROVISIONAL = 540.0
V_LIMIT = 0.95 * VDC_PROVISIONAL / math.sqrt(3.0)
ID_REF = 0.0
IQ_REF_HIGH = 112.43
IQ_REF_LOW = 0.0
T_LOAD = 0.0

CSV_PATH = Path("experiments/b1_8_foc_recovery.csv")
OUT_DIR = Path("experiments/b1_8_foc_recovery_analysis")


def main():
    if CSV_PATH.exists() or OUT_DIR.exists():
        raise FileExistsError(
            "Existe una salida B1.8; no se sobrescribirá."
        )

    plant = PMSMBase()
    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
        voltage_limit=V_LIMIT,
    )

    observed = {
        "pi_d": 0.0,
        "pi_q": 0.0,
        "requested_d": 0.0,
        "requested_q": 0.0,
        "aw_calls": 0,
    }

    original_update = foc.current_controller.update
    original_decoupling = foc.decoupling.apply
    original_aw = foc.current_controller.apply_conditional_anti_windup

    def update_probe(**kwargs):
        vd, vq = original_update(**kwargs)
        observed["pi_d"] = vd
        observed["pi_q"] = vq
        return vd, vq

    def decoupling_probe(**kwargs):
        vd, vq = original_decoupling(**kwargs)
        observed["requested_d"] = vd
        observed["requested_q"] = vq
        return vd, vq

    def aw_probe(**kwargs):
        observed["aw_calls"] += 1
        return original_aw(**kwargs)

    foc.current_controller.update = update_probe
    foc.decoupling.apply = decoupling_probe
    foc.current_controller.apply_conditional_anti_windup = aw_probe

    output = plant.step(
        PlantInput(va=0.0, vb=0.0, vc=0.0, t_load=T_LOAD),
        dt=DT,
    )

    rows = []
    n_steps = int(round(T_END / DT))
    for k in range(n_steps):
        t = (k + 1) * DT
        iq_ref = IQ_REF_HIGH if t < T_RELEASE else IQ_REF_LOW
        aw_before = observed["aw_calls"]

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

        theta_e = mechanical_to_electrical_angle(
            output.theta_m, foc.pole_pairs
        )
        v_alpha, v_beta = clarke_transform(va, vb, vc)
        vd_applied, vq_applied = park_transform(
            v_alpha, v_beta, theta_e
        )

        vd_req = observed["requested_d"]
        vq_req = observed["requested_q"]
        v_req_mag = math.hypot(vd_req, vq_req)
        v_applied_mag = math.hypot(vd_applied, vq_applied)

        output = plant.step(
            PlantInput(va=va, vb=vb, vc=vc, t_load=T_LOAD),
            dt=DT,
        )

        rows.append({
            "t": t,
            "phase": "high_reference" if t < T_RELEASE else "recovery",
            "id_ref": ID_REF,
            "id": output.id,
            "iq_ref": iq_ref,
            "iq": output.iq,
            "iq_error": iq_ref - output.iq,
            "vd_pi": observed["pi_d"],
            "vq_pi": observed["pi_q"],
            "vd_requested": vd_req,
            "vq_requested": vq_req,
            "v_requested_mag": v_req_mag,
            "vd_applied": vd_applied,
            "vq_applied": vq_applied,
            "v_applied_mag": v_applied_mag,
            "v_limit": V_LIMIT,
            "saturated": int(v_req_mag > V_LIMIT),
            "anti_windup_called": int(observed["aw_calls"] > aw_before),
            "int_id": foc.current_controller.int_id,
            "int_iq": foc.current_controller.int_iq,
            "te": output.te,
            "omega_m": output.omega_m,
            "va": va,
            "vb": vb,
            "vc": vc,
        })

    OUT_DIR.mkdir(parents=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    t_ms = np.array([r["t"] for r in rows]) * 1000
    iq = np.array([r["iq"] for r in rows])
    iq_ref = np.array([r["iq_ref"] for r in rows])
    id_meas = np.array([r["id"] for r in rows])
    v_req = np.array([r["v_requested_mag"] for r in rows])
    v_app = np.array([r["v_applied_mag"] for r in rows])
    v_lim = np.array([r["v_limit"] for r in rows])
    sat = np.array([r["saturated"] for r in rows], dtype=bool)
    aw = np.array([r["anti_windup_called"] for r in rows], dtype=bool)
    int_d = np.array([r["int_id"] for r in rows])
    int_q = np.array([r["int_iq"] for r in rows])
    speed = np.array([r["omega_m"] for r in rows])
    torque = np.array([r["te"] for r in rows])
    release_ms = T_RELEASE * 1000

    def save_figure(fig, stem):
        fig.tight_layout()
        fig.savefig(OUT_DIR / f"{stem}.png", dpi=180)
        fig.savefig(OUT_DIR / f"{stem}.pdf")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, iq_ref, "--", label="Referencia iq")
    ax.plot(t_ms, iq, label="Medición iq")
    ax.axvline(release_ms, color="black", linestyle=":", label="Retiro de referencia")
    ax.set(
        xlabel="Tiempo (ms)", ylabel="Corriente (A)",
        title="B1.8 — Respuesta al retirar la referencia de corriente",
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, "b1_8_current_recovery")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, v_req, label="Magnitud solicitada dq")
    ax.plot(t_ms, v_app, label="Magnitud aplicada dq")
    ax.plot(t_ms, v_lim, "--", label="Límite configurado")
    ax.axvline(release_ms, color="black", linestyle=":", label="Retiro de referencia")
    if sat.any():
        ax.fill_between(t_ms, 0, v_lim, where=sat, alpha=0.12,
                        label="Muestras saturadas")
    ax.set(
        xlabel="Tiempo (ms)", ylabel="Tensión dq (V)",
        title="B1.8 — Tensión solicitada y aplicada",
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, "b1_8_voltage_saturation")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, int_d, label="int_id")
    ax.plot(t_ms, int_q, label="int_iq")
    if aw.any():
        ax.scatter(t_ms[aw], int_q[aw], s=9, label="Llamada anti-windup")
    ax.axvline(release_ms, color="black", linestyle=":", label="Retiro de referencia")
    ax.set(
        xlabel="Tiempo (ms)", ylabel="Estado integral (A·s)",
        title="B1.8 — Integradores y llamadas al anti-windup",
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    save_figure(fig, "b1_8_integrators_antiwindup")

    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.plot(t_ms, speed, label="Velocidad mecánica")
    ax1.set_xlabel("Tiempo (ms)")
    ax1.set_ylabel("Velocidad mecánica (rad/s)")
    ax1.axvline(release_ms, color="black", linestyle=":")
    ax2 = ax1.twinx()
    ax2.plot(t_ms, torque, label="Par electromagnético", color="tab:orange")
    ax2.set_ylabel("Par electromagnético (Nm)")
    lines = ax1.get_lines()[:1] + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")
    ax1.set_title("B1.8 — Evolución mecánica durante la prueba")
    ax1.grid(True, alpha=0.3)
    save_figure(fig, "b1_8_speed_torque")

    high = np.array([r["t"] < T_RELEASE for r in rows])
    recovery = ~high
    rmse_all = float(np.sqrt(np.mean((iq_ref - iq) ** 2)))
    rmse_high = float(np.sqrt(np.mean((iq_ref[high] - iq[high]) ** 2)))
    rmse_recovery = float(np.sqrt(np.mean((iq_ref[recovery] - iq[recovery]) ** 2)))
    release_idx = int(np.flatnonzero(recovery)[0])
    iq_at_release = float(iq[release_idx])
    max_abs_iq_recovery = float(np.max(np.abs(iq[recovery])))
    final_iq = float(iq[-1])
    final_abs_error = abs(final_iq - IQ_REF_LOW)
    recovery_tol = 5.0

    # Primer punto posterior a la liberación desde el cual todas las muestras
    # restantes permanecen dentro de ±5 A. Si no ocurre, se registra como tal.
    within = np.abs(iq[recovery] - IQ_REF_LOW) <= recovery_tol
    settle_index = None
    for j in range(len(within)):
        if np.all(within[j:]):
            settle_index = j
            break
    if settle_index is None:
        settle_text = "No alcanzado dentro de la ventana de recuperación."
    else:
        settle_ms = t_ms[release_idx + settle_index] - release_ms
        settle_text = f"{settle_ms:.6f} ms después del retiro de referencia."

    sat_count = int(sat.sum())
    aw_count = int(aw.sum())
    max_applied = float(v_app.max())
    max_requested = float(v_req.max())
    max_id = float(np.max(np.abs(id_meas)))
    max_speed = float(np.max(np.abs(speed)))
    max_torque = float(np.max(np.abs(torque)))

    report = f"""# B1.8 — Recuperación de corriente tras retirar referencia alta

## Objetivo
Observar la respuesta de la planta y del FOC activo al retirar una referencia
alta de corriente. Este ensayo no constituye por sí mismo una validación física.

## Condiciones
- Controlador: `pmsm_hybrid_control.foc.foc.FOC`.
- Paso: {DT} s.
- Duración: {T_END} s.
- Referencia id: {ID_REF} A.
- Referencia iq: {IQ_REF_HIGH} A antes de {T_RELEASE} s; {IQ_REF_LOW} A desde ese instante.
- Carga: {T_LOAD} Nm.
- VDC experimental provisional: {VDC_PROVISIONAL} V.
- Límite vectorial configurado: {V_LIMIT:.6f} V.
- La referencia alta supera el límite de corriente nominal indicado para el motor;
  se trata de una condición de estrés, no de un punto de operación validado.
- La instrumentación envuelve métodos de esta instancia; no modifica los módulos
  de producción.
- Tensión solicitada: capturada después del desacoplamiento.
- Tensión aplicada: reconstruida desde va, vb, vc mediante Clarke/Park.

## Resultados calculados
- Muestras: {len(rows)}.
- RMSE global de iq: {rmse_all:.6f} A.
- RMSE antes de retirar la referencia: {rmse_high:.6f} A.
- RMSE durante la recuperación: {rmse_recovery:.6f} A.
- iq al primer punto posterior al retiro: {iq_at_release:.6f} A.
- Máximo |iq| durante recuperación: {max_abs_iq_recovery:.6f} A.
- iq final: {final_iq:.6f} A.
- Error absoluto final respecto a 0 A: {final_abs_error:.6f} A.
- Criterio exploratorio de asentamiento: |iq| ≤ {recovery_tol:.1f} A de forma sostenida.
- Tiempo hasta cumplir el criterio: {settle_text}
- Máximo |id|: {max_id:.6f} A.
- Máximo |omega_m|: {max_speed:.6f} rad/s.
- Máximo |Te|: {max_torque:.6f} Nm.
- Máxima magnitud de tensión solicitada: {max_requested:.6f} V.
- Máxima magnitud de tensión aplicada: {max_applied:.6f} V.
- Muestras marcadas saturadas: {sat_count}.
- Muestras con llamada al anti-windup: {aw_count}.
- Exceso máximo de tensión aplicada sobre el límite: {max(0.0, max_applied-V_LIMIT):.9f} V.

## Archivos generados
- `b1_8_current_recovery.png/pdf`
- `b1_8_voltage_saturation.png/pdf`
- `b1_8_integrators_antiwindup.png/pdf`
- `b1_8_speed_torque.png/pdf`
- CSV fuente: `{CSV_PATH}`.

## Limitaciones e interpretación
La llamada al anti-windup indica ejecución del método, no demuestra por sí sola
que la estrategia mejore el desempeño. La referencia alta es una demanda de
estrés y no debe interpretarse como operación admisible del motor. VDC=540 V
es provisional. La prueba usa la planta simulada y no datos experimentales del
motor real. El umbral de ±5 A es un criterio exploratorio definido para esta
prueba, no una especificación del fabricante.
"""
    (OUT_DIR / "README_B1_8.md").write_text(report, encoding="utf-8")

    print("===== B1.8 — RESULTADOS =====")
    print(f"VDC provisional       = {VDC_PROVISIONAL:.3f} V")
    print(f"Límite de tensión     = {V_LIMIT:.6f} V")
    print(f"Muestras              = {len(rows)}")
    print(f"RMSE iq global        = {rmse_all:.6f} A")
    print(f"RMSE iq referencia alta = {rmse_high:.6f} A")
    print(f"RMSE iq recuperación  = {rmse_recovery:.6f} A")
    print(f"iq al liberar         = {iq_at_release:.6f} A")
    print(f"iq final              = {final_iq:.6f} A")
    print(f"Error final respecto a 0 A = {final_abs_error:.6f} A")
    print(f"Asentamiento ±5 A     = {settle_text}")
    print(f"Máx. |v solicitada|   = {max_requested:.6f} V")
    print(f"Máx. |v aplicada|     = {max_applied:.6f} V")
    print(f"Muestras saturadas    = {sat_count}")
    print(f"Llamadas anti-windup  = {aw_count}")
    print(f"CSV                   = {CSV_PATH}")
    print(f"Figuras e informe     = {OUT_DIR}")


if __name__ == "__main__":
    main()
