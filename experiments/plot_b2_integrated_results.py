import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("experiments")
OUTPUT = ROOT / "b2_integrated_analysis"
OUTPUT.mkdir(parents=True, exist_ok=True)

CASES = [
    ("b2_2_speed_closed_loop.csv", "B2.2", False),
    ("b2_3_speed_load_steps.csv", "B2.3", True),
]

def read_csv(path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"CSV vacío: {path}")
    return rows

def values(rows, key):
    return [float(row[key]) for row in rows]

def save(fig, stem):
    fig.tight_layout()
    fig.savefig(OUTPUT / f"{stem}.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUTPUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)

def plot_case(filename, label, has_load):
    rows = read_csv(ROOT / filename)
    t = [x * 1000 for x in values(rows, "t")]

    # 1. Velocidad: referencia y respuesta.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t, values(rows, "omega_ref"), label="Referencia")
    ax.plot(t, values(rows, "omega_m"), label="Medida simulada")
    ax.set(xlabel="Tiempo (ms)", ylabel="Velocidad mecánica (rad/s)",
           title=f"{label} — Seguimiento de velocidad")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save(fig, f"{label.lower()}_speed")

    # 2. Corriente q: referencia y respuesta.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t, values(rows, "iq_ref"), label="Referencia")
    ax.plot(t, values(rows, "iq"), label="Corriente simulada")
    ax.set(xlabel="Tiempo (ms)", ylabel="Corriente q (A)",
           title=f"{label} — Corriente q")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save(fig, f"{label.lower()}_iq")

    # 3. Par electromagnético y, cuando exista, par de carga.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t, values(rows, "te"), label="Par electromagnético")
    if has_load:
        ax.plot(t, values(rows, "t_load"), label="Par de carga")
    ax.set(xlabel="Tiempo (ms)", ylabel="Par (N·m)",
           title=f"{label} — Respuesta de par")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save(fig, f"{label.lower()}_torque")

    # 4. Tensiones trifásicas registradas en el CSV.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for key in ("va", "vb", "vc"):
        ax.plot(t, values(rows, key), label=key)
    ax.set(xlabel="Tiempo (ms)", ylabel="Tensión (V)",
           title=f"{label} — Tensiones trifásicas aplicadas")
    ax.grid(True, alpha=0.3)
    ax.legend()
    save(fig, f"{label.lower()}_phase_voltages")

    print(f"{label}: {len(rows)} muestras; figuras PNG/PDF generadas.")

def main():
    for filename, label, has_load in CASES:
        plot_case(filename, label, has_load)
    print(f"Salida: {OUTPUT}")

if __name__ == "__main__":
    main()
