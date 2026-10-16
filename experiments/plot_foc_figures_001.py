from pathlib import Path
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "foc_figures_001"

CASES = {
    "B0.1": ROOT / "experiments/b0_1_current_iq_step.csv",
    "B0.2": ROOT / "experiments/b0_2_current_iq_step.csv",
    "B1.5": ROOT / "experiments/b1_5_iq_reference_steps.csv",
    "B1.6": ROOT / "experiments/b1_6_current_load_steps.csv",
}

def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"No existe el CSV requerido: {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames or []
    if not rows:
        raise ValueError(f"CSV vacío: {path}")
    data = {}
    for col in columns:
        try:
            data[col] = np.asarray([float(r[col]) for r in rows])
        except (ValueError, TypeError):
            pass
    if "t" not in data:
        raise ValueError(f"El CSV no contiene una columna numérica 't': {path}")
    return data

def require(data, columns, case):
    missing = [c for c in columns if c not in data]
    if missing:
        raise ValueError(f"{case}: faltan columnas {missing}")

def save(fig, stem):
    # Nunca sobrescribir un resultado anterior.
    for ext in (".png", ".pdf"):
        target = OUT / f"{stem}{ext}"
        if target.exists():
            raise FileExistsError(f"Se evita sobrescribir: {target}")
    fig.savefig(OUT / f"{stem}.png", dpi=200, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"FIGURA: {stem}.png y {stem}.pdf")

def current_tracking(case, d):
    require(d, ["id_ref", "id", "iq_ref", "iq"], case)
    t_ms = d["t"] * 1000
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax[0].plot(t_ms, d["id_ref"], label=r"$i_d^*$")
    ax[0].plot(t_ms, d["id"], label=r"$i_d$")
    ax[0].set_ylabel("Corriente d (A)")
    ax[0].grid(True, alpha=0.3)
    ax[0].legend()

    ax[1].plot(t_ms, d["iq_ref"], label=r"$i_q^*$")
    ax[1].plot(t_ms, d["iq"], label=r"$i_q$")
    ax[1].set_ylabel("Corriente q (A)")
    ax[1].set_xlabel("Tiempo (ms)")
    ax[1].grid(True, alpha=0.3)
    ax[1].legend()

    fig.suptitle(f"{case} — seguimiento de corrientes")
    fig.tight_layout()
    save(fig, f"{case.lower()}_current_tracking")

def voltage_margin(case, d):
    require(d, ["vd", "vq", "v_dq", "v_max"], case)
    t_ms = d["t"] * 1000
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax[0].plot(t_ms, d["vd"], label=r"$v_d$")
    ax[0].plot(t_ms, d["vq"], label=r"$v_q$")
    ax[0].set_ylabel("Tensión dq (V)")
    ax[0].grid(True, alpha=0.3)
    ax[0].legend()

    ax[1].plot(t_ms, d["v_dq"], label=r"$|v_{dq}|$")
    ax[1].plot(t_ms, d["v_max"], "--", label=r"$v_{\max}$")
    ax[1].set_ylabel("Magnitud de tensión (V)")
    ax[1].set_xlabel("Tiempo (ms)")
    ax[1].grid(True, alpha=0.3)
    ax[1].legend()

    fig.suptitle(f"{case} — tensión de control y límite registrado")
    fig.tight_layout()
    save(fig, f"{case.lower()}_voltage_margin")

def b15_steps(d):
    require(d, ["iq_ref", "iq", "id_ref", "id"], "B1.5")
    current_tracking("B1.5", d)

def b16_load_response(d):
    require(d, ["t_load", "te", "omega_m", "iq_ref", "iq"], "B1.6")
    t = d["t"] * 1000
    fig, ax = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

    ax[0].plot(t, d["t_load"], label=r"$T_{load}$")
    ax[0].set_ylabel("Carga (Nm)")
    ax[0].legend()
    ax[0].grid(True, alpha=0.3)

    ax[1].plot(t, d["te"], label=r"$T_e$")
    ax[1].set_ylabel("Par electromagnético (Nm)")
    ax[1].legend()
    ax[1].grid(True, alpha=0.3)

    ax[2].plot(t, d["iq_ref"], label=r"$i_q^*$")
    ax[2].plot(t, d["iq"], label=r"$i_q$")
    ax[2].set_ylabel("Corriente q (A)")
    ax[2].legend()
    ax[2].grid(True, alpha=0.3)

    ax[3].plot(t, d["omega_m"], label=r"$\omega_m$")
    ax[3].set_ylabel("Velocidad (rad/s)")
    ax[3].set_xlabel("Tiempo (ms)")
    ax[3].legend()
    ax[3].grid(True, alpha=0.3)

    fig.suptitle("B1.6 — respuesta del sistema ante cambios de carga")
    fig.tight_layout()
    save(fig, "b1_6_load_response")

def main():
    if not OUT.is_dir():
        raise FileNotFoundError(f"No existe el directorio de salida: {OUT}")
    data = {case: load_csv(path) for case, path in CASES.items()}

    # Genera figuras de seguimiento y, cuando hay datos, margen de tensión.
    for case in ("B0.1", "B0.2"):
        current_tracking(case, data[case])
        voltage_margin(case, data[case])

    b15_steps(data["B1.5"])
    b16_load_response(data["B1.6"])

    print("\n===== RESUMEN NUMÉRICO DE LOS CSV =====")
    for case, d in data.items():
        print(f"{case}: {len(d['t'])} muestras; "
              f"t=[{d['t'][0]:.6g}, {d['t'][-1]:.6g}] s")
        if "v_dq" in d and "v_max" in d:
            excess = np.max(d["v_dq"] - d["v_max"])
            ratio = np.max(d["v_dq"] / np.maximum(d["v_max"], 1e-12))
            print(f"  max(|v_dq|-v_max) = {excess:.6g} V")
            print(f"  max(|v_dq|/v_max) = {ratio:.6g}")

    print(f"\nFiguras guardadas en: {OUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
