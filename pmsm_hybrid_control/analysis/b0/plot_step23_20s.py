import csv
from pathlib import Path

import matplotlib.pyplot as plt


INPUT = Path("results/b0/step23_20s/trajectory.csv")
OUTPUT = Path("results/b0/step23_20s/figuras")


def load_csv():
    with INPUT.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return {
        key: [float(row[key]) for row in rows]
        for key in reader.fieldnames
    }


def save(fig, name):
    path = OUTPUT / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"OK  {path}")


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"No existe: {INPUT}")

    OUTPUT.mkdir(parents=True, exist_ok=True)

    d = load_csv()

    t = d["t"]
    omega_ref = d["omega_ref"]
    omega = d["omega_m"]
    error_w = d["error_w"]

    iq = d["iq"]
    iq_ref = d["iq_ref"]
    id_current = d["id"]

    te = d["te"]
    t_load = d["t_load"]

    vd = d["vd"]
    vq = d["vq"]
    v_dq = d["v_dq"]

    duty_a = d["duty_a"]
    duty_b = d["duty_b"]
    duty_c = d["duty_c"]

    # ============================================================
    # 1. Respuesta completa 0-20 s
    # ============================================================
    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(t, omega, label="ωm")
    ax.plot(t, omega_ref, "--", label="ωref")

    ax.axvline(0.05, linestyle=":", label="Escalón de carga")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Velocidad mecánica [rad/s]")
    ax.set_title("B0 — Respuesta de velocidad, 0–20 s")
    ax.grid(True)
    ax.legend()

    save(fig, "01_velocidad_0_20s.png")

    # ============================================================
    # 2. Evento de carga: velocidad + error
    # ============================================================
    mask = [
        0.045 <= x <= 0.20
        for x in t
    ]

    tevent = [x for x, m in zip(t, mask) if m]
    wevent = [x for x, m in zip(omega, mask) if m]
    erevent = [x for x, m in zip(error_w, mask) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tevent, wevent, label="ωm")
    ax.plot(tevent, [omega_ref[0]] * len(tevent), "--", label="ωref")

    ax.axvline(0.05, linestyle=":", label="Carga = 23 Nm")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Velocidad [rad/s]")
    ax.set_title("B0 — Transitorio ante escalón de carga")
    ax.grid(True)
    ax.legend()

    save(fig, "02_evento_carga_velocidad.png")

    # ============================================================
    # 3. Evento de carga: iq + iq_ref + torque
    # ============================================================
    iqevent = [x for x, m in zip(iq, mask) if m]
    iqrefevent = [x for x, m in zip(iq_ref, mask) if m]
    teevent = [x for x, m in zip(te, mask) if m]
    tloadevent = [x for x, m in zip(t_load, mask) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tevent, iqevent, label="iq")
    ax.plot(tevent, iqrefevent, "--", label="iq_ref")
    ax.plot(tevent, teevent, label="Te [Nm]")
    ax.plot(tevent, tloadevent, "--", label="Tload [Nm]")

    ax.axvline(0.05, linestyle=":", label="t = 0.05 s")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Magnitud")
    ax.set_title("B0 — Corriente y torque durante el evento")
    ax.grid(True)
    ax.legend()

    save(fig, "03_evento_carga_corriente_torque.png")

    # ============================================================
    # 4. Régimen final 18-20 s
    # ============================================================
    mask_final = [
        18.0 <= x <= 20.0
        for x in t
    ]

    tfinal = [x for x, m in zip(t, mask_final) if m]
    wfinal = [x for x, m in zip(omega, mask_final) if m]
    wref_final = [x for x, m in zip(omega_ref, mask_final) if m]
    efinal = [x for x, m in zip(error_w, mask_final) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, wfinal, label="ωm")
    ax.plot(tfinal, wref_final, "--", label="ωref")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Velocidad [rad/s]")
    ax.set_title("B0 — Régimen final, 18–20 s")
    ax.grid(True)
    ax.legend()

    save(fig, "04_regimen_final_velocidad.png")

    # ============================================================
    # 5. Error de velocidad final
    # ============================================================
    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, efinal, label="eω")

    ax.axhline(0.0, linestyle="--")
    ax.axhline(0.01 * omega_ref[-1], linestyle=":")
    ax.axhline(-0.01 * omega_ref[-1], linestyle=":")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Error [rad/s]")
    ax.set_title("B0 — Error de velocidad, 18–20 s")
    ax.grid(True)
    ax.legend()

    save(fig, "05_regimen_final_error.png")

    # ============================================================
    # 6. Corrientes finales
    # ============================================================
    ifinal = [x for x, m in zip(id_current, mask_final) if m]
    iqfinal = [x for x, m in zip(iq, mask_final) if m]
    iqreffinal = [x for x, m in zip(iq_ref, mask_final) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, ifinal, label="id")
    ax.plot(tfinal, iqfinal, label="iq")
    ax.plot(tfinal, iqreffinal, "--", label="iq_ref")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Corriente [A]")
    ax.set_title("B0 — Corrientes en régimen final")
    ax.grid(True)
    ax.legend()

    save(fig, "06_regimen_final_corrientes.png")

    # ============================================================
    # 7. Torque final
    # ============================================================
    tefinal = [x for x, m in zip(te, mask_final) if m]
    tlfinal = [x for x, m in zip(t_load, mask_final) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, tefinal, label="Te")
    ax.plot(tfinal, tlfinal, "--", label="Tload")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Torque [Nm]")
    ax.set_title("B0 — Torque en régimen final")
    ax.grid(True)
    ax.legend()

    save(fig, "07_regimen_final_torque.png")

    # ============================================================
    # 8. Voltaje dq final
    # ============================================================
    vd_final = [x for x, m in zip(vd, mask_final) if m]
    vq_final = [x for x, m in zip(vq, mask_final) if m]
    vdq_final = [x for x, m in zip(v_dq, mask_final) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, vd_final, label="Vd")
    ax.plot(tfinal, vq_final, label="Vq")
    ax.plot(tfinal, vdq_final, label="|Vdq|")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Voltaje [V]")
    ax.set_title("B0 — Voltaje dq en régimen final")
    ax.grid(True)
    ax.legend()

    save(fig, "08_regimen_final_voltaje.png")

    # ============================================================
    # 9. PWM final
    # ============================================================
    da_final = [x for x, m in zip(duty_a, mask_final) if m]
    db_final = [x for x, m in zip(duty_b, mask_final) if m]
    dc_final = [x for x, m in zip(duty_c, mask_final) if m]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(tfinal, da_final, label="Duty A")
    ax.plot(tfinal, db_final, label="Duty B")
    ax.plot(tfinal, dc_final, label="Duty C")

    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Duty")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("B0 — PWM en régimen final")
    ax.grid(True)
    ax.legend()

    save(fig, "09_regimen_final_pwm.png")

    print()
    print("=" * 58)
    print(" B0 — GRÁFICAS GENERADAS")
    print("=" * 58)
    print(f"directorio = {OUTPUT}")
    print("figuras    = 9")
    print("=" * 58)


if __name__ == "__main__":
    main()
