import csv
from pathlib import Path

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.transforms.clarke import inverse_clarke_transform
from pmsm_hybrid_control.transforms.park import inverse_park_transform


DT = 50e-6
T_END = 0.100

VD = 0.0
VQ = 1.0
T_LOAD = 0.0

OUTPUT = Path("experiments/b0_9_plant_speed_response.csv")


def main():
    plant = PMSMBase()

    rows = []

    n_steps = int(round(T_END / DT))

    for k in range(n_steps + 1):
        time_s = k * DT

        theta_m = plant.states["theta_m"]
        theta_e = plant.params.n_pole_pairs * theta_m

        alpha, beta = inverse_park_transform(
            VD,
            VQ,
            theta_e,
        )

        va, vb, vc = inverse_clarke_transform(
            alpha,
            beta,
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

        rows.append(
            {
                "time_s": time_s,
                "vd_V": VD,
                "vq_V": VQ,
                "t_load_Nm": T_LOAD,
                "va_V": va,
                "vb_V": vb,
                "vc_V": vc,
                "id_A": output.id,
                "iq_A": output.iq,
                "te_Nm": output.te,
                "omega_m_rad_s": output.omega_m,
                "theta_m_rad": output.theta_m,
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    iq_values = [row["iq_A"] for row in rows]
    id_values = [row["id_A"] for row in rows]
    te_values = [row["te_Nm"] for row in rows]
    omega_values = [row["omega_m_rad_s"] for row in rows]

    print("========================================")
    print(" B0.9 — PLANT SPEED RESPONSE")
    print("========================================")
    print(f"dt          = {DT:.9f} s")
    print(f"T_END       = {T_END:.6f} s")
    print(f"vd          = {VD:.6f} V")
    print(f"vq          = {VQ:.6f} V")
    print(f"T_load      = {T_LOAD:.6f} N*m")
    print()
    print(f"iq final    = {iq_values[-1]:.9f} A")
    print(f"|iq| max    = {max(abs(x) for x in iq_values):.9f} A")
    print(f"|id| max    = {max(abs(x) for x in id_values):.9f} A")
    print(f"Te final    = {te_values[-1]:.9f} N*m")
    print(f"Te max      = {max(te_values):.9f} N*m")
    print(f"omega final = {omega_values[-1]:.9f} rad/s")
    print(f"omega max   = {max(omega_values):.9f} rad/s")
    print()
    print(f"CSV         = {OUTPUT}")


if __name__ == "__main__":
    main()
