"""Planta base PMSM (M4_BASE).

Representacion matematica/comportamental del modelo M4 confirmado
(FEM-Parameterized PMSM, parameterization=constantMutualInductance).
NO es un solver FEM (ver 06_KIMI_BUILD_RULES.md#7).

Modelo dinamico en coordenadas dq (convencion QleadsD_AphaseToDaxis):

    d(id)/dt = (vd - Rs*id + we*Lq*iq) / Ld
    d(iq)/dt = (vq - Rs*iq - we*(Ld*id + lambda_m)) / Lq
    Te       = (3/2) * p * (lambda_m*iq + (Ld - Lq)*id*iq)   [REFERENCIA]
    d(wm)/dt = (Te - T_load) / J
    d(tm)/dt = wm

La ecuacion de Te es una ECUACION DE REFERENCIA/CANDIDATA clasica
(03_IMPLEMENTATION_PLAN.md / PROMPT MAESTRO #13): NO se afirma que sea la
ley interna exacta de Simscape M4 sin evidencia adicional.

ESTADO DEL MODELO MECANICO: B (amortiguamiento viscoso) y Tfric (friccion)
son PENDING VERIFICATION y NO se incluyen en el balance de torque.
Se asume que T_load representa el torque total resistente externo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .parameters import PMSMParameters, default_m4_parameters


@dataclass
class PlantInput:
    """Entradas de la planta — PROPOSED INTERNAL INTERFACE
    (02_CONTRACTS.md#5.1; NO son nombres de buses CloudE)."""
    va: float = 0.0       # tension fase A [V]
    vb: float = 0.0       # tension fase B [V]
    vc: float = 0.0       # tension fase C [V]
    t_load: float = 0.0   # torque de carga total [N*m] (incluye lo que B/Tfric cubririan)
    theta_m: float = 0.0  # posicion mecanica [rad]


@dataclass
class PlantOutput:
    """Salidas de la planta — PROPOSED INTERNAL INTERFACE (02_CONTRACTS.md#5.2)."""
    ia: float = 0.0        # A
    ib: float = 0.0        # A
    ic: float = 0.0        # A
    id: float = 0.0        # A (eje d)
    iq: float = 0.0        # A (eje q)
    omega_m: float = 0.0   # rad/s (mecanica)
    theta_m: float = 0.0   # rad (mecanica)
    te: float = 0.0        # N*m


class PMSMBase:
    """Planta PMSM base (M4_BASE).

    Estados internos: id, iq (electrico); omega_m, theta_m (mecanico).
    Independiente de CloudE: no importa CONTROL_BUS/REF_BUS/ADAPT_BUS.
    """

    def __init__(self, params: PMSMParameters | None = None) -> None:
        self.params = params if params is not None else default_m4_parameters()
        self.params.validate()
        # Estados iniciales CONFIRMED AS CONFIGURATION: i_d=0, i_q=0, w=0, theta=0
        self._id = 0.0
        self._iq = 0.0
        self._omega_m = 0.0     # rad/s
        self._theta_m = 0.0     # rad

    # -- angulos ----------------------------------------------------------
    @property
    def theta_e(self) -> float:
        """Angulo electrico [rad]. theta_e = p * theta_m (p = 4, CONFIRMED)."""
        return self.params.n_pole_pairs * self._theta_m

    # -- torque -----------------------------------------------------------
    def electromagnetic_torque(self, id_: float | None = None, iq: float | None = None) -> float:
        """Torque electromagnetico [N*m] — ECUACION DE REFERENCIA.

        Te = (3/2) * p * (lambda_m*iq + (Ld - Lq)*id*iq)
        Con Ld = Lq el segundo termino se anula matematicamente, pero la
        estructura completa se conserva como referencia (PROMPT MAESTRO #13).
        """
        p = self.params
        i_d = self._id if id_ is None else id_
        i_q = self._iq if iq is None else iq
        return 1.5 * p.n_pole_pairs * (p.lambda_m * i_q + (p.ld - p.lq) * i_d * i_q)

    # -- derivadas --------------------------------------------------------
    def _derivatives(self, vd: float, vq: float, t_load: float,
                     omega_e: float) -> tuple[float, float, float, float]:
        p = self.params
        di_d = (vd - p.rs * self._id + omega_e * p.lq * self._iq) / p.ld
        di_q = (vq - p.rs * self._iq - omega_e * (p.ld * self._id + p.lambda_m)) / p.lq
        te = self.electromagnetic_torque()
        # NOTA: B y Tfric son PENDING VERIFICATION -> NO incluidos (ver docstring).
        d_omega = (te - t_load) / p.j
        d_theta = self._omega_m
        return di_d, di_q, d_omega, d_theta

    # -- paso de integracion ----------------------------------------------
    def step(self, inp: PlantInput, dt: float) -> PlantOutput:
        """Integra un paso con Euler explicito (suficiente para consistencia
        de software en Phase 1; metodo numerico = PROPOSED)."""
        if dt <= 0:
            raise ValueError("dt debe ser positivo")
        from pmsm_hybrid_control.transforms.park import park_transform, inverse_park_transform

        theta_e = self.params.n_pole_pairs * inp.theta_m
        # Consistencia: la entrada theta_m se usa como posicion del rotor.
        self._theta_m = inp.theta_m

        # abc -> dq0
        v_d, v_q = park_transform(*_clarke_amplitude(inp.va, inp.vb, inp.vc), theta_e)

        omega_e = self.params.n_pole_pairs * self._omega_m
        k1 = self._derivatives(v_d, v_q, inp.t_load, omega_e)
        self._id += k1[0] * dt
        self._iq += k1[1] * dt
        self._omega_m += k1[2] * dt
        self._theta_m += k1[3] * dt

        # dq0 -> abc para las corrientes de salida
        i_a, i_b, i_c = _inverse_clarke_amplitude(*inverse_park_transform(self._id, self._iq, theta_e))

        return PlantOutput(
            ia=i_a, ib=i_b, ic=i_c,
            id=self._id, iq=self._iq,
            omega_m=self._omega_m, theta_m=self._theta_m,
            te=self.electromagnetic_torque(),
        )

    # -- acceso a estados ---------------------------------------------------
    @property
    def states(self) -> dict[str, float]:
        return {"id": self._id, "iq": self._iq,
                "omega_m": self._omega_m, "theta_m": self._theta_m}


def _clarke_amplitude(ia: float, ib: float, ic: float) -> tuple[float, float]:
    """Clarke invariante en amplitud, con i_a+i_b+i_c=0.
    (Implementacion local en abc; la version canonica esta en transforms/clarke.py)"""
    i_alpha = ia
    i_beta = (ib - ic) / np.sqrt(3.0)
    return float(i_alpha), float(i_beta)


def _inverse_clarke_amplitude(i_alpha: float, i_beta: float) -> tuple[float, float, float]:
    i_a = i_alpha
    i_b = -0.5 * i_alpha + (np.sqrt(3.0) / 2.0) * i_beta
    i_c = -0.5 * i_alpha - (np.sqrt(3.0) / 2.0) * i_beta
    return float(i_a), float(i_b), float(i_c)
