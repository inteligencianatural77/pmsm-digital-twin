import csv
from pathlib import Path

import matplotlib.pyplot as plt


CSV_PATH = Path("experiments/b0_8_plant_vq_reversal.csv")
OUT_DIR = Path("experiments/b0_8_analysis")

def find_vq_transition_time(time_s, vq):
    for i in range(1, len(vq)):
        if vq[i] != vq[i - 1]:
            return time_s[i]
    return None


def find_speed_zero_crossing(time_s, speed):
    for i in range(1, len(speed)):
        w0 = speed[i - 1]
        w1 = speed[i]

        if w0 * w1 < 0:
            return time_s[i - 1] - w0 * (
                time_s[i] - time_s[i - 1]
            ) / (w1 - w0)

    return None


def load_csv(path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"El CSV está vacío: {path}")

    required = {
        "time_s",
        "vq_V",
        "id_A",
        "iq_A",
        "te_Nm",
        "omega_m_rad_s",
        "theta_m_rad",
    }

    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"Faltan columnas en el CSV: {sorted(missing)}")

    data = {
        key: [float(row[key]) for row in rows]
        for key in required
    }

    return data


def decorate(ax, ylabel):
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encuentra {CSV_PATH}")

    data = load_csv(CSV_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    time_s = data["time_s"]
    t_ms = [t * 1000 for t in time_s]

    vq_transition = find_vq_transition_time(
        time_s,
        data["vq_V"],
    )
    speed_zero = find_speed_zero_crossing(
        time_s,
        data["omega_m_rad_s"],
    )

    figures = [
        (
            "b0_8_currents.png",
            "Corrientes del motor — B0.8",
            [
                ("id_A", "id (A)"),
                ("iq_A", "iq (A)"),
            ],
        ),
        (
            "b0_8_torque.png",
            "Par electromagnético — B0.8",
            [("te_Nm", "Te (N·m)")],
        ),
        (
            "b0_8_speed.png",
            "Velocidad mecánica — B0.8",
            [("omega_m_rad_s", "ωm (rad/s)")],
        ),
        (
            "b0_8_position.png",
            "Posición mecánica — B0.8",
            [("theta_m_rad", "θm (rad)")],
        ),
    ]

    for filename, title, series in figures:
        fig, ax = plt.subplots(figsize=(10, 5))

        for key, label in series:
            ax.plot(t_ms, data[key], label=label)

        if filename == "b0_8_speed.png":
            ax.axhline(0, color="black", linewidth=0.8)

            if speed_zero is not None:
                ax.axvline(
                    speed_zero * 1000,
                    linestyle=":",
                    label=f"Cruce interpolado ({speed_zero * 1000:.3f} ms)",
                )

        if vq_transition is not None:
            ax.axvline(
                vq_transition * 1000,
                linestyle="--",
                label=f"Inversión de vq ({vq_transition * 1000:.3f} ms)",
            )

        decorate(
            ax,
            "Corriente (A)"
            if filename == "b0_8_currents.png"
            else series[0][1],
        )
        ax.set_xlabel("Tiempo (ms)")
        ax.set_title(title)
        fig.tight_layout()

        output = OUT_DIR / filename
        fig.savefig(output, dpi=160)
        plt.close(fig)
        print(f"Gráfica: {output}")

    print(f"\nMuestras analizadas: {len(t_ms)}")
    print(f"Intervalo: {t_ms[0]:.6f} a {t_ms[-1]:.6f} ms")
    print(f"Directorio de salida: {OUT_DIR}")


if __name__ == "__main__":
    main()
