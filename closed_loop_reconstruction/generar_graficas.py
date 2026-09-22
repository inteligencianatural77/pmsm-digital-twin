#!/usr/bin/env python3
"""
Generación reproducible de las 7 gráficas del experimento
lazo_cerrado_m3_foc_m4.py.

Entrada:
    closed_loop_reconstruction/resultado_lazo_cerrado.csv

Salida:
    closed_loop_reconstruction/figuras/*.png
"""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


BASE = Path(__file__).resolve().parent
CSV_FILE = BASE / "resultado_lazo_cerrado.csv"
OUT_DIR = BASE / "figuras"


def cargar_csv():
    with CSV_FILE.open("r", newline="") as f:
        reader = csv.DictReader(f)
        columnas = reader.fieldnames

        datos = {col: [] for col in columnas}

        for row in reader:
            for col in columnas:
                datos[col].append(float(row[col]))

    return datos


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(OUT_DIR / nombre, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    datos = cargar_csv()

    t = datos["t"]

    # 01 — Velocidad
    fig, ax = plt.subplots()
    ax.plot(t, datos["omega_ref"], label="omega_ref")
    ax.plot(t, datos["omega_m"], label="omega_m")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Velocidad [rad/s]")
    ax.set_title("Velocidad mecánica y referencia")
    ax.grid(True)
    ax.legend()
    guardar(fig, "01_velocidad.png")

    # 02 — Error de velocidad
    fig, ax = plt.subplots()
    ax.plot(t, datos["omega_error"])
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Error [rad/s]")
    ax.set_title("Error de velocidad")
    ax.grid(True)
    guardar(fig, "02_error_velocidad.png")

    # 03 — Corrientes d-q
    fig, ax = plt.subplots()
    ax.plot(t, datos["id"], label="id")
    ax.plot(t, datos["iq"], label="iq")
    ax.plot(t, datos["id_ref"], "--", label="id_ref")
    ax.plot(t, datos["iq_ref"], "--", label="iq_ref")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Corriente [A]")
    ax.set_title("Corrientes en marco d-q")
    ax.grid(True)
    ax.legend()
    guardar(fig, "03_corrientes_dq.png")

    # 04 — Torque
    fig, ax = plt.subplots()
    ax.plot(t, datos["Te"], label="Te")
    ax.plot(t, datos["Tload"], label="Tload")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.set_title("Torque electromagnético y carga")
    ax.grid(True)
    ax.legend()
    guardar(fig, "04_torque.png")

    # 05 — Tensiones d-q
    fig, ax = plt.subplots()
    ax.plot(t, datos["Vd"], label="Vd")
    ax.plot(t, datos["Vq"], label="Vq")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Tensión [V]")
    ax.set_title("Tensiones en marco d-q")
    ax.grid(True)
    ax.legend()
    guardar(fig, "05_tensiones_dq.png")

    # 06 — Duty cycles
    fig, ax = plt.subplots()
    ax.plot(t, datos["duty_a"], label="duty_a")
    ax.plot(t, datos["duty_b"], label="duty_b")
    ax.plot(t, datos["duty_c"], label="duty_c")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Duty")
    ax.set_title("Duty cycles")
    ax.grid(True)
    ax.legend()
    guardar(fig, "06_duty.png")

    # 07 — iq y límites
    fig, ax = plt.subplots()
    ax.plot(t, datos["iq"], label="iq")
    ax.plot(t, datos["iq_ref"], "--", label="iq_ref")
    ax.axhline(112.43, linestyle="--", label="iq_max")
    ax.axhline(-112.43, linestyle="--", label="iq_min")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Corriente [A]")
    ax.set_title("iq y límites de corriente")
    ax.grid(True)
    ax.legend()
    guardar(fig, "07_iq_limites.png")

    print("=" * 70)
    print("GENERACIÓN DE GRÁFICAS — P4")
    print("=" * 70)
    print(f"Entrada : {CSV_FILE}")
    print(f"Salida  : {OUT_DIR}")
    print()
    for i in range(1, 8):
        archivo = OUT_DIR / f"{i:02d}_"
        encontrados = list(OUT_DIR.glob(f"{i:02d}_*.png"))
        if encontrados:
            print(f"OK      : {encontrados[0].name}")


if __name__ == "__main__":
    main()
