"""Diagnostico del defecto pre-D-08.

Mide lo que el FOC ve (Clarke+Park con theta_m publicado) frente al
id/iq reales de la planta y lo compara con la prediccion analitica:

    id_visto = id*cos(d) + iq*sin(d)
    iq_visto = -id*sin(d) + iq*cos(d)

    d = p*omega_m*dt

Este ensayo describe el comportamiento PRE-D-08.
No es un test pass/fail ni modifica la planta.
"""

import math

from pmsm_hybrid_control.plant.pmsm_base import PMSMBase, PlantInput
from pmsm_hybrid_control.transforms.clarke import clarke_transform
from pmsm_hybrid_control.transforms.park import park_transform


DT = 50e-6
ID0 = 0.0
IQ0 = 10.0


print(
    f"{'omega0':>9} "
    f"{'d[rad]':>9} "
    f"{'id_real':>10} "
    f"{'id_FOC':>10} "
    f"{'id_pred_pre':>12} "
    f"{'iq_real':>10} "
    f"{'iq_FOC':>10}"
)

for omega0 in (68.773872, 309.218699, 696.0, 1385.0):
    plant = PMSMBase()

    plant._id = ID0
    plant._iq = IQ0
    plant._omega_m = omega0
    plant._theta_m = 1.234

    p = plant.params.n_pole_pairs

    out = plant.step(
        PlantInput(
            va=0.0,
            vb=0.0,
            vc=0.0,
            t_load=0.0,
        ),
        DT,
    )

    d = p * omega0 * DT

    i_alpha, i_beta = clarke_transform(
        out.ia,
        out.ib,
        out.ic,
    )

    id_foc, iq_foc = park_transform(
        i_alpha,
        i_beta,
        p * out.theta_m,
    )

    id_pred = out.id * math.cos(d) + out.iq * math.sin(d)
    iq_pred = -out.id * math.sin(d) + out.iq * math.cos(d)

    print(
        f"{omega0:9.3f} "
        f"{d:9.5f} "
        f"{out.id:10.5f} "
        f"{id_foc:10.5f} "
        f"{id_pred:12.5f} "
        f"{out.iq:10.5f} "
        f"{iq_foc:10.5f}"
    )

    print(
        f"          iq_pred_pre={iq_pred:10.5f} "
        f"|err_id|={abs(id_foc - id_pred):.3e} "
        f"|err_iq|={abs(iq_foc - iq_pred):.3e}"
    )
