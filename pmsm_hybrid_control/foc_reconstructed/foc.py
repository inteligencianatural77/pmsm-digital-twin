"""FOC reconstruido desde el M6 FOC_CORE de CloudE.

La arquitectura mantiene:
- PI de velocidad
- PI de corriente d/q
- desacoplamiento
- limitación de iq
- limitación de tensión
- anti-windup

El FOC sigue siendo el controlador principal.
ANFIS queda fuera de este módulo.
"""

from __future__ import annotations

from .current_controller import CurrentController
from .decoupling import Decoupling


class FOC:
    """Controlador FOC reconstruido del M6."""

    def __init__(
        self,
        *,
        ld: float = 0.0012,
        lq: float = 0.0012,
        lambda_m: float = 0.1100,
        pole_pairs: int = 4,
        kp_speed: float = 5.2804,
        ki_speed: float = 1.2693,
        ts_current: float = 50e-6,
        ts_speed: float = 200e-6,
        iq_max: float = 112.4300,
        iq_min: float = -112.4300,
    ) -> None:

        self.ld = ld
        self.lq = lq
        self.lambda_m = lambda_m
        self.pole_pairs = pole_pairs

        self.kp_speed = kp_speed
        self.ki_speed = ki_speed

        self.ts_current = ts_current
        self.ts_speed = ts_speed

        self.iq_max = iq_max
        self.iq_min = iq_min

        self.int_speed = 0.0
        self.speed_counter = 0

        self.current = CurrentController()
        self.decoupling = Decoupling()

    def reset(self) -> None:
        self.int_speed = 0.0
        self.speed_counter = 0
        self.current.reset()

    def step(
        self,
        omega_ref: float,
        omega_m: float,
        id_: float,
        iq: float,
        vdc: float,
        dt: float | None = None,
    ) -> tuple[float, float, float, float]:

        dt = self.ts_current if dt is None else dt

        self.speed_counter += 1

        if self.speed_counter * dt >= self.ts_speed:
            self.speed_counter = 0

            error_w = omega_ref - omega_m

            self.int_speed += error_w * self.ts_speed

            iq_raw = (
                self.kp_speed * error_w
                + self.ki_speed * self.int_speed
            )

            iq_ref = max(
                self.iq_min,
                min(self.iq_max, iq_raw),
            )

            if iq_ref != iq_raw:
                self.int_speed -= error_w * self.ts_speed
        else:
            if not hasattr(self, "_iq_ref"):
                iq_ref = 0.0
            else:
                iq_ref = self._iq_ref

        self._iq_ref = iq_ref
        id_ref = 0.0

        omega_e = self.pole_pairs * omega_m

        vd_dec, vq_dec = self.decoupling.apply(
            id_=id_,
            iq=iq,
            omega_e=omega_e,
            ld=self.ld,
            lq=self.lq,
            lambda_m=self.lambda_m,
        )

        v_max = max(1.0, float(vdc)) / (3.0 ** 0.5) * 0.95

        self.current.voltage_limit = v_max

        vd, vq = self.current.update(
            id_ref=id_ref,
            iq_ref=iq_ref,
            id_meas=id_,
            iq_meas=iq,
            dt=dt,
            decoupling_d=vd_dec,
            decoupling_q=vq_dec,
        )

        return vd, vq, id_ref, iq_ref
