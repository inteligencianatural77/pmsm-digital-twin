"""B1.7 — Instrumentación externa de saturación vectorial del FOC activo.

No modifica los módulos de producción.
VDC=540 V es una condición experimental provisional, no una especificación
confirmada del motor.
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
VDC_PROVISIONAL = 540.0
V_LIMIT = 0.95 * VDC_PROVISIONAL / math.sqrt(3.0)
ID_REF = 0.0
IQ_REF = 112.43
T_LOAD = 0.0

CSV_PATH = Path("experiments/b1_7_foc_voltage_saturation.csv")
OUT_DIR = Path("experiments/b1_7_foc_saturation_analysis")


def main():
    if CSV_PATH.exists() or OUT_DIR.exists():
        raise FileExistsError(
            "Existe una salida B1.7; no se sobrescribirá."
        )

    plant = PMSMBase()
    foc = FOC(
        ld=plant.params.ld,
        lq=plant.params.lq,
        lambda_m=plant.params.lambda_m,
        pole_pairs=plant.params.n_pole_pairs,
        voltage_limit=V_LIMIT,
    )

    # Instrumentación externa: envolvemos métodos de esta instancia,
    # sin modificar los archivos ni las clases de producción.
    observed = {
        "pi_d": 0.0, "pi_q": 0.0,
        "requested_d": 0.0, "requested_q": 0.0,
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
    for k in range(int(round(T_END / DT))):
        t = (k + 1) * DT
        aw_before = observed["aw_calls"]

        va, vb, vc = foc.step(
            ia=output.ia,
            ib=output.ib,
            ic=output.ic,
            theta_m=output.theta_m,
            omega_m=output.omega_m,
            id_ref=ID_REF,
            iq_ref=IQ_REF,
            dt=DT,
        )

        # Reconstruye la tensión dq realmente aplicada desde la salida abc.
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
            "id_ref": ID_REF,
            "id": output.id,
            "iq_ref": IQ_REF,
            "iq": output.iq,
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
            "va": va, "vb": vb, "vc": vc,
        })

    with CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    OUT_DIR.mkdir(parents=True)

    t_ms = np.array([r["t"] for r in rows]) * 1000
    iq = np.array([r["iq"] for r in rows])
    iq_ref = np.array([r["iq_ref"] for r in rows])
    v_req = np.array([r["v_requested_mag"] for r in rows])
    v_app = np.array([r["v_applied_mag"] for r in rows])
    v_lim = np.array([r["v_limit"] for r in rows])
    sat = np.array([r["saturated"] for r in rows], dtype=bool)
    int_d = np.array([r["int_id"] for r in rows])
    int_q = np.array([r["int_iq"] for r in rows])
    aw = np.array([r["anti_windup_called"] for r in rows], dtype=bool)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, iq_ref, "--", label="Referencia iq")
    ax.plot(t_ms, iq, label="Medición iq")
    ax.set(xlabel="Tiempo (ms)", ylabel="Corriente (A)",
           title="B1.7 — Seguimiento de corriente con límite vectorial")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "b1_7_current_tracking.png", dpi=180)
    fig.savefig(OUT_DIR / "b1_7_current_tracking.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, v_req, label="Magnitud solicitada dq")
    ax.plot(t_ms, v_app, label="Magnitud aplicada dq")
    ax.plot(t_ms, v_lim, "--", label="Límite configurado")
    if sat.any():
        ax.fill_between(t_ms, 0, v_lim, where=sat,
                        alpha=0.12, label="Muestras con saturación")
    ax.set(xlabel="Tiempo (ms)", ylabel="Tensión dq (V)",
           title="B1.7 — Saturación vectorial")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "b1_7_voltage_saturation.png", dpi=180)
    fig.savefig(OUT_DIR / "b1_7_voltage_saturation.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t_ms, int_d, label="int_id")
    ax.plot(t_ms, int_q, label="int_iq")
    if aw.any():
        ax.scatter(t_ms[aw], int_q[aw], s=9, label="Llamada anti-windup")
    ax.set(xlabel="Tiempo (ms)", ylabel="Estado integral (A·s)",
           title="B1.7 — Integradores y llamadas al anti-windup")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "b1_7_integrators_antiwindup.png", dpi=180)
    fig.savefig(OUT_DIR / "b1_7_integrators_antiwindup.pdf")
    plt.close(fig)

    rmse = float(np.sqrt(np.mean((iq_ref - iq) ** 2)))
    report = f"""# B1.7 — Saturación vectorial y anti-windup

## Condiciones
- FOC: implementación activa `pmsm_hybrid_control.foc.foc.FOC`.
- dt: {DT} s; duración nominal: {T_END} s.
- Referencia id: {ID_REF} A; referencia iq: {IQ_REF} A.
- Carga: {T_LOAD} Nm.
- VDC experimental provisional: {VDC_PROVISIONAL} V.
- Límite configurado: {V_LIMIT:.6f} V.
- La tensión solicitada se captura después del desacoplamiento.
- La tensión aplicada se reconstruye desde va, vb, vc usando Clarke/Park.
- La instrumentación envuelve métodos de la instancia durante la prueba;
  no modifica los módulos de producción.

## Resultados calculados
- Muestras: {len(rows)}.
- RMSE global de iq: {rmse:.6f} A.
- Máxima magnitud solicitada dq: {v_req.max():.6f} V.
- Máxima magnitud aplicada dq: {v_app.max():.6f} V.
- Límite configurado: {V_LIMIT:.6f} V.
- Muestras marcadas como saturadas: {int(sat.sum())}.
- Muestras con llamada al anti-windup: {int(aw.sum())}.
- Máximo exceso aplicado sobre el límite: {max(0.0, float(v_app.max()-V_LIMIT)):.9f} V.

## Archivos
- `b1_7_current_tracking.png/pdf`
- `b1_7_voltage_saturation.png/pdf`
- `b1_7_integrators_antiwindup.png/pdf`

CSV fuente: `experiments/b1_7_foc_voltage_saturation.csv`.

## Limitaciones
Este es un ensayo de simulación funcional, no una validación frente a medidas
del motor real. VDC=540 V es provisional. La llamada al anti-windup indica
que se ejecutó el método; no prueba por sí sola que la estrategia sea óptima.
La tensión aplicada reconstruida puede tener pequeñas diferencias numéricas
respecto del límite por transformaciones y redondeo.
"""
    (OUT_DIR / "README_B1_7.md").write_text(report, encoding="utf-8")

    print("===== B1.7 — RESULTADOS =====")
    print(f"VDC provisional = {VDC_PROVISIONAL:.3f} V")
    print(f"V_LIMIT         = {V_LIMIT:.6f} V")
    print(f"Muestras        = {len(rows)}")
    print(f"RMSE iq         = {rmse:.6f} A")
    print(f"Máx. |v solicitado| = {v_req.max():.6f} V")
    print(f"Máx. |v aplicado|  = {v_app.max():.6f} V")
    print(f"Muestras saturadas = {int(sat.sum())}")
    print(f"Llamadas anti-windup = {int(aw.sum())}")
    print(f"CSV: {CSV_PATH}")
    print(f"Figuras e informe: {OUT_DIR}")


if __name__ == "__main__":
    main()
