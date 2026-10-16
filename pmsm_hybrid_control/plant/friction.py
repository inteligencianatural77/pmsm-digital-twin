from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class StribeckFrictionParameters:
    """
    Parámetros de un escenario experimental de fricción no lineal.

    Estos parámetros NO representan todavía parámetros confirmados
    del motor Siemens 1FT7087.
    """

    tc: float
    ts: float
    omega_s: float
    delta: float
    b: float

    def __post_init__(self) -> None:
        if self.tc < 0.0:
            raise ValueError("tc debe ser >= 0")
        if self.ts < 0.0:
            raise ValueError("ts debe ser >= 0")
        if self.ts < self.tc:
            raise ValueError("ts debe ser >= tc")
        if self.omega_s <= 0.0:
            raise ValueError("omega_s debe ser > 0")
        if self.delta <= 0.0:
            raise ValueError("delta debe ser > 0")
        if self.b < 0.0:
            raise ValueError("b debe ser >= 0")


class StribeckFriction:
    """
    Modelo experimental de fricción Coulomb + Stribeck + viscosa.

    Tf(omega) =
        Tc*sign(omega)
        + (Ts-Tc)*exp(-(abs(omega)/omega_s)^delta)
        + B*omega

    Convención:
        Tf tiene el mismo signo que omega y, por tanto,
        se resta de la dinámica mecánica.
    """

    def __init__(self, params: StribeckFrictionParameters) -> None:
        self.params = params

    def torque(self, omega_m: float) -> float:
        if not math.isfinite(omega_m):
            raise ValueError("omega_m debe ser finito")

        p = self.params

        if omega_m == 0.0:
            sign = 0.0
        elif omega_m > 0.0:
            sign = 1.0
        else:
            sign = -1.0

        magnitude = abs(omega_m)

        stribeck = (
            (p.ts - p.tc)
            * math.exp(-((magnitude / p.omega_s) ** p.delta))
        )

        coulomb = p.tc * sign
        viscous = p.b * omega_m

        return coulomb + stribeck * sign + viscous
