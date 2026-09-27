import csv
import math
from pathlib import Path


INPUT = Path("results/b0/step23_20s/trajectory.csv")
OUTPUT = Path("results/b0/step23_20s/metrics.csv")


def rms(values):
    if not values:
        return float("nan")
    return math.sqrt(sum(x * x for x in values) / len(values))


def mean_abs(values):
    if not values:
        return float("nan")
    return sum(abs(x) for x in values) / len(values)


def max_abs(values):
    if not values:
        return float("nan")
    return max(abs(x) for x in values)


def percentile_abs(values, percentile):
    values = sorted(abs(x) for x in values)

    if not values:
        return float("nan")

    index = (len(values) - 1) * percentile
    low = math.floor(index)
    high = math.ceil(index)

    if low == high:
        return values[low]

    fraction = index - low
    return values[low] + fraction * (values[high] - values[low])


def fmt(value):
    return f"{value:.12g}"


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"No existe: {INPUT}")

    rows = []

    with INPUT.open(newline="") as f:
        reader = csv.DictReader(f)

        for raw in reader:
            row = {key: float(value) for key, value in raw.items()}
            rows.append(row)

    if not rows:
        raise RuntimeError("trajectory.csv está vacío")

    t = [r["t"] for r in rows]
    omega_ref = [r["omega_ref"] for r in rows]
    omega = [r["omega_m"] for r in rows]
    error_w = [r["error_w"] for r in rows]

    iq = [r["iq"] for r in rows]
    iq_ref = [r["iq_ref"] for r in rows]
    error_iq = [r["error_iq"] for r in rows]
    id_values = [r["id"] for r in rows]

    te = [r["te"] for r in rows]
    torque_error = [r["torque_error"] for r in rows]

    vd = [r["vd"] for r in rows]
    vq = [r["vq"] for r in rows]
    v_dq = [r["v_dq"] for r in rows]

    duty_a = [r["duty_a"] for r in rows]
    duty_b = [r["duty_b"] for r in rows]
    duty_c = [r["duty_c"] for r in rows]

    duty_all = duty_a + duty_b + duty_c

    # ------------------------------------------------------------
    # Ventana final: últimos 10 %
    # ------------------------------------------------------------
    t_final = t[-1]
    final_window_start = 0.90 * t_final

    final_rows = [
        r for r in rows
        if r["t"] >= final_window_start
    ]

    final_error_w = [r["error_w"] for r in final_rows]
    final_torque_error = [r["torque_error"] for r in final_rows]
    final_iq_error = [r["error_iq"] for r in final_rows]

    # ------------------------------------------------------------
    # Evento de carga: t = 0.05 s
    # ------------------------------------------------------------
    event_time = 0.05
    pre_event = min(
        rows,
        key=lambda r: abs(r["t"] - (event_time - 0.001))
    )
    event = min(
        rows,
        key=lambda r: abs(r["t"] - event_time)
    )
    post_event = min(
        rows,
        key=lambda r: abs(r["t"] - (event_time + 0.001))
    )

    # ------------------------------------------------------------
    # Tiempo de establecimiento.
    #
    # Criterio B0:
    # |error_w| <= 1 % de omega_ref final
    # y permanece dentro de la banda hasta el final.
    # ------------------------------------------------------------
    final_ref = omega_ref[-1]
    settling_band = 0.01 * abs(final_ref)

    settling_time = float("nan")

    # Búsqueda O(N): recorrer hacia atrás hasta encontrar
    # la última muestra que todavía viola la banda.
    last_outside = None

    for i in range(len(rows) - 1, -1, -1):
        if abs(rows[i]["error_w"]) > settling_band:
            last_outside = i
            break

    if last_outside is None:
        settling_time = rows[0]["t"]
    elif last_outside + 1 < len(rows):
        settling_time = rows[last_outside + 1]["t"]

    # ------------------------------------------------------------
    # PWM fuera de rango
    # ------------------------------------------------------------
    pwm_out_of_range = sum(
        1
        for value in duty_all
        if value < 0.0 or value > 1.0
    )

    # ------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------
    metrics = [
        ("samples", len(rows)),
        ("duration_s", t[-1]),
        ("dt_s", t[1] - t[0] if len(t) > 1 else float("nan")),

        ("omega_ref_rad_s", omega_ref[-1]),
        ("omega_final_rad_s", omega[-1]),
        ("omega_error_final_rad_s", error_w[-1]),
        ("omega_error_final_pct_ref", 100.0 * abs(error_w[-1]) / abs(omega_ref[-1])),

        ("omega_error_max_abs_rad_s", max_abs(error_w)),
        ("omega_error_rms_rad_s", rms(error_w)),
        ("omega_error_mae_rad_s", mean_abs(error_w)),
        ("omega_error_p95_abs_rad_s", percentile_abs(error_w, 0.95)),

        ("settling_time_1pct_s", settling_time),
        ("settling_band_1pct_rad_s", settling_band),

        ("iq_final_A", iq[-1]),
        ("iq_ref_final_A", iq_ref[-1]),
        ("iq_error_final_A", error_iq[-1]),
        ("iq_max_abs_A", max_abs(iq)),
        ("iq_ref_max_abs_A", max_abs(iq_ref)),
        ("iq_error_rms_A", rms(error_iq)),

        ("id_final_A", id_values[-1]),
        ("id_max_abs_A", max_abs(id_values)),

        ("te_final_Nm", te[-1]),
        ("te_max_abs_Nm", max_abs(te)),
        ("torque_error_final_Nm", torque_error[-1]),
        ("torque_error_rms_Nm", rms(torque_error)),
        ("torque_error_max_abs_Nm", max_abs(torque_error)),

        ("vd_max_abs_V", max_abs(vd)),
        ("vq_max_abs_V", max_abs(vq)),
        ("v_dq_max_V", max(v_dq)),
        ("v_dq_rms_V", rms(v_dq)),

        ("duty_min", min(duty_all)),
        ("duty_max", max(duty_all)),
        ("pwm_out_of_range_samples", pwm_out_of_range),

        ("final_window_start_s", final_window_start),
        ("final_window_error_rms_rad_s", rms(final_error_w)),
        ("final_window_error_max_abs_rad_s", max_abs(final_error_w)),
        ("final_window_torque_error_rms_Nm", rms(final_torque_error)),
        ("final_window_iq_error_rms_A", rms(final_iq_error)),

        ("event_pre_omega_rad_s", pre_event["omega_m"]),
        ("event_pre_iq_A", pre_event["iq"]),
        ("event_pre_te_Nm", pre_event["te"]),
        ("event_pre_error_w_rad_s", pre_event["error_w"]),

        ("event_omega_rad_s", event["omega_m"]),
        ("event_iq_A", event["iq"]),
        ("event_te_Nm", event["te"]),
        ("event_error_w_rad_s", event["error_w"]),

        ("event_post_omega_rad_s", post_event["omega_m"]),
        ("event_post_iq_A", post_event["iq"]),
        ("event_post_te_Nm", post_event["te"]),
        ("event_post_error_w_rad_s", post_event["error_w"]),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])

        for name, value in metrics:
            writer.writerow([name, fmt(value)])

    # ------------------------------------------------------------
    # Resumen de terminal
    # ------------------------------------------------------------
    print()
    print("=" * 58)
    print(" B0 — MÉTRICAS STEP 23 Nm / 20 s")
    print("=" * 58)

    print(f"samples                 = {len(rows)}")
    print(f"duration                = {t[-1]:.6f} s")
    print(f"dt                      = {t[1] - t[0]:.9g} s")

    print()
    print("VELOCIDAD")
    print(f"omega_ref               = {omega_ref[-1]:.9f} rad/s")
    print(f"omega_final             = {omega[-1]:.9f} rad/s")
    print(f"error_final             = {error_w[-1]:.9f} rad/s")
    print(f"error_final_rel         = {100.0 * abs(error_w[-1]) / abs(omega_ref[-1]):.9f} %")
    print(f"error_max_abs           = {max_abs(error_w):.9f} rad/s")
    print(f"error_RMS               = {rms(error_w):.9f} rad/s")
    print(f"settling_1pct           = {settling_time:.9f} s")

    print()
    print("CORRIENTE")
    print(f"iq_final                = {iq[-1]:.9f} A")
    print(f"iq_ref_final            = {iq_ref[-1]:.9f} A")
    print(f"iq_error_final          = {error_iq[-1]:.9f} A")
    print(f"iq_max_abs              = {max_abs(iq):.9f} A")
    print(f"id_final                = {id_values[-1]:.9f} A")
    print(f"id_max_abs              = {max_abs(id_values):.9f} A")

    print()
    print("TORQUE")
    print(f"Te_final                = {te[-1]:.9f} Nm")
    print(f"Te-Tload final          = {torque_error[-1]:.12f} Nm")
    print(f"torque_error_RMS        = {rms(torque_error):.12f} Nm")
    print(f"torque_error_max_abs    = {max_abs(torque_error):.12f} Nm")

    print()
    print("VOLTAJE / PWM")
    print(f"|Vdq|_max               = {max(v_dq):.9f} V")
    print(f"|Vdq|_RMS               = {rms(v_dq):.9f} V")
    print(f"duty_min                = {min(duty_all):.9f}")
    print(f"duty_max                = {max(duty_all):.9f}")
    print(f"PWM fuera [0,1]         = {pwm_out_of_range}")

    print()
    print("EVENTO t = 0.05 s")
    print(f"pre  omega / iq / Te    = {pre_event['omega_m']:.6f} / {pre_event['iq']:.6f} / {pre_event['te']:.6f}")
    print(f"event omega / iq / Te   = {event['omega_m']:.6f} / {event['iq']:.6f} / {event['te']:.6f}")
    print(f"post omega / iq / Te    = {post_event['omega_m']:.6f} / {post_event['iq']:.6f} / {post_event['te']:.6f}")

    print()
    print(f"metrics = {OUTPUT}")
    print("=" * 58)


if __name__ == "__main__":
    main()
