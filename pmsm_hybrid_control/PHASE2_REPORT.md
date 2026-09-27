========================================
PHASE 2 REPORT — MAPAS NO LINEALES
========================================
STATUS:            COMPLETA (avance por instruccion explicita del usuario)

IMPLEMENTED:
- plant/flux_maps.py: FluxMap con base analitica PROPOSED derivada de
  parametros M4 CONFIRMED (psi_d = Ld*id + lambda_m; psi_q = Lq*iq),
  coherente con parametrizacion constantMutualInductance CONFIRMADA.
  Sin dependencia de theta (sin saliencia, Ld=Lq CONFIRMED).
- plant/torque_map.py: TorqueMap con la ECUACION DE REFERENCIA
  Te = (3/2)p(lambda_m iq + (Ld-Lq)id iq) (REFERENCIA, no ley interna Simscape).
- recovered_m4_tables(): tablas del .slx (dfluxdiMatrix, dfluxdxMatrix,
  TorqueMatrix, Ld/LqMatrix, PmMatrix, matrices 3D/dq0/IBX, coeficientes
  de perdidas) cargadas como RECOVERED / ACTIVE STATUS = PENDING VERIFICATION.
  Activarlas con use_recovered_tables=True LANZA NotImplementedError.

FILES CREATED/MODIFIED: plant/flux_maps.py, plant/torque_map.py (reescritos),
tests/test_maps.py (6 tests), PHASE2_REPORT.md.

DECISION CLAVE: los mapas activos son la representacion interna PROPOSED
mas simple consistente con los datos M4 confirmados; las tablas recuperadas
permanecen visibles pero inactivas hasta verificacion (regla 02_CONTRACTS#7.1).

PENDING: semantica activa de matrices 3D/dq0/IBX bajo constantMutualInductance;
PmMatrix vs lambda_m; rotorLossCoeff (perdidas NO modeladas, loss_param=none
CONFIRMED como configuracion).

NEXT STEP: Phase 3 — DATASET + ENTRENAMIENTO ANFIS (objetivo fisico aun
PENDING VERIFICATION; candidatos conceptuales X=[id,iq,theta], Y=[psi_d,psi_q,Te]).
