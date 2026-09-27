"""PI de corriente dq reconstruido a partir del M6/Foc Core de CloudE."""

from __future__ import annotations


class CurrentController:
    """PI discreto de corriente d/q con anti-windup por rollback."""

    def __init__(
        self,
        kp_id: float = 15.0796,
        ki_id: float = 628.3185,
        kp_iq: float = 15.0796,
        ki_iq: float = 628.3185,
        voltage_limit: float | None = None,
    ) -> None:
        self.kp_id = kp_id
        self.ki_id = ki_id
        self.kp_iq = kp_iq
        self.ki_iq = ki_iq
        self.voltage_limit = voltage_limit

        self.int_id = 0.0
        self.int_iq = 0.0

    def reset(self) -> None:
        self.int_id = 0.0
        self.int_iq = 0.0

    def update(
        self,
        id_ref: float,
        iq_ref: float,
        id_meas: float,
        iq_meas: float,
        dt: float,
        decoupling_d: float = 0.0,
        decoupling_q: float = 0.0,
    ) -> tuple[float, float]:

        error_id = id_ref - id_meas
        error_iq = iq_ref - iq_meas

        self.int_id += error_id * dt
        self.int_iq += error_iq * dt

        vd_raw = (
            self.kp_id * error_id
            + self.ki_id * self.int_id
            + decoupling_d
        )

        vq_raw = (
            self.kp_iq * error_iq
            + self.ki_iq * self.int_iq
            + decoupling_q
        )

        if self.voltage_limit is None:
            return vd_raw, vq_raw

        vd = max(-self.voltage_limit, min(self.voltage_limit, vd_raw))
        vq = max(-self.voltage_limit, min(self.voltage_limit, vq_raw))

        if vd != vd_raw:
            self.int_id -= error_id * dt

        if vq != vq_raw:
            self.int_iq -= error_iq * dt

        return vd, vq
