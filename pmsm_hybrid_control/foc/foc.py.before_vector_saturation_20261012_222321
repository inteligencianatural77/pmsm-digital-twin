"""FOC activo — B1.3.

Composición del lazo de corriente dq:

    abc corriente
        -> Clarke
        -> Park
        -> PI de corriente
        -> desacoplamiento dq
        -> inversa de Park
        -> inversa de Clarke
        -> abc tensión

B1.3 NO implementa todavía el lazo de velocidad ni la conexión directa
con PMSMBase. Es un componente de control de corriente aislado.

Convención:
    QleadsD_AphaseToDaxis

El flujo magnético permanente, inductancias y número de pares de polos
se reciben explícitamente. No se utilizan valores históricos implícitos.

lambda_m M4:
    0.107245 Wb

Los valores de ganancias PI por defecto corresponden a la referencia
histórica/documental M6 y NO son parámetros de la planta M4.
"""

from __future__ import annotations

from pmsm_hybrid_control.foc.current_controller import CurrentController
from pmsm_hybrid_control.foc.decoupling import Decoupling
from pmsm_hybrid_control.transforms.clarke import (
    clarke_transform,
    inverse_clarke_transform,
)
from pmsm_hybrid_control.transforms.park import (
    inverse_park_transform,
    mechanical_to_electrical_angle,
    park_transform,
)


class FOCNotImplementedError(NotImplementedError):
    """Compatibilidad con la interfaz placeholder histórica."""

    pass


class FOC:
    """FOC de corriente dq, sin lazo de velocidad."""

    def __init__(
        self,
        ld: float,
        lq: float,
        lambda_m: float,
        pole_pairs: int,
        kp_id: float = 15.0796,
        ki_id: float = 628.3185,
        kp_iq: float = 15.0796,
        ki_iq: float = 628.3185,
        voltage_limit: float | None = None,
    ) -> None:
        if ld <= 0.0:
            raise ValueError("ld debe ser positivo")

        if lq <= 0.0:
            raise ValueError("lq debe ser positivo")

        if pole_pairs <= 0:
            raise ValueError("pole_pairs debe ser positivo")

        self.ld = float(ld)
        self.lq = float(lq)
        self.lambda_m = float(lambda_m)
        self.pole_pairs = int(pole_pairs)

        self.current_controller = CurrentController(
            kp_id=kp_id,
            ki_id=ki_id,
            kp_iq=kp_iq,
            ki_iq=ki_iq,
            voltage_limit=voltage_limit,
        )

        self.decoupling = Decoupling()

    def reset(self) -> None:
        """Reinicia los integradores del PI de corriente."""
        self.current_controller.reset()

    def step(
        self,
        ia: float,
        ib: float,
        ic: float,
        theta_m: float,
        omega_m: float,
        id_ref: float,
        iq_ref: float,
        dt: float,
    ) -> tuple[float, float, float]:
        """Ejecuta un paso del FOC de corriente.

        Entradas:
            ia, ib, ic: corrientes de fase [A]
            theta_m: posicion mecanica [rad]
            omega_m: velocidad mecanica [rad/s]
            id_ref, iq_ref: referencias dq [A]
            dt: periodo de muestreo [s]

        Salidas:
            va, vb, vc: tensiones de fase [V]
        """
        if dt <= 0.0:
            raise ValueError("dt debe ser positivo")

        theta_e = mechanical_to_electrical_angle(
            theta_m,
            n_pole_pairs=self.pole_pairs,
        )

        omega_e = self.pole_pairs * float(omega_m)

        # abc -> alpha-beta
        i_alpha, i_beta = clarke_transform(
            float(ia),
            float(ib),
            float(ic),
        )

        # alpha-beta -> dq
        id_meas, iq_meas = park_transform(
            i_alpha,
            i_beta,
            theta_e,
        )

        # PI de corriente.
        # El desacoplamiento se aplica SOLO después del PI para evitar
        # contabilizarlo dos veces.
        vd_pi, vq_pi = self.current_controller.update(
            id_ref=id_ref,
            iq_ref=iq_ref,
            id_meas=id_meas,
            iq_meas=iq_meas,
            dt=dt,
        )

        # Compensación cruzada PMSM.
        vd, vq = self.decoupling.apply(
            vd_pi=vd_pi,
            vq_pi=vq_pi,
            id_=id_meas,
            iq=iq_meas,
            omega_e=omega_e,
            ld=self.ld,
            lq=self.lq,
            lambda_m=self.lambda_m,
        )

        # dq -> alpha-beta
        v_alpha, v_beta = inverse_park_transform(
            vd,
            vq,
            theta_e,
        )

        # alpha-beta -> abc
        va, vb, vc = inverse_clarke_transform(
            v_alpha,
            v_beta,
        )

        return float(va), float(vb), float(vc)
