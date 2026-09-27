# pmsm_hybrid_control

Migracion progresiva del modelo PMSM 1FT7087 (M4 Physical Plant) desde MATLAB/Simulink/Simscape hacia Python modular.

## Estado actual

- **Phase 0**: esqueleto del proyecto (estructura + imports + placeholders) — COMPLETA
- **Phase 1**: M4_BASE (parametros confirmados + planta base + transformadas + tests) — COMPLETA
- **Phase 2**: MAPAS (base analitica PROPOSED desde parametros M4 CONFIRMED; tablas recuperadas del .slx visibles pero INACTIVAS / PENDING VERIFICATION) — COMPLETA
- Phase 3+ (ANFIS, M4_NONLINEAR, FOC, GOVERNOR, SAFETY, CLOUDE ADAPTER): **NO IMPLEMENTADAS**.

## Fuentes de datos (jerarquia obligatoria)

| Fuente | Uso |
|---|---|
| `01_M4_HARD_DATA.md` | UNICA fuente de parametros M4 confirmados |
| `02_CONTRACTS.md` | Contratos de señales entre modulos |
| `05_CLOUDE_FORENSIC_REFERENCE.md` | SOLO referencia arquitectonica/historica |
| CloudE | NUNCA fuente de parametros M4 (lambda_m CloudE = 0.11 != M4 = 0.107245) |

## Parametros PENDING (no inventados)

- `B` (amortiguamiento viscoso) — PENDING VERIFICATION
- `Tfric` (torque de friccion) — PENDING VERIFICATION
- Procedencia de `lambda_m = 0.107245` — CONFIRMED valor / PENDING provenance
- Tolerancias de validacion fisica — PENDING (los tests actuales son de consistencia de software)

## Uso

```bash
pip install -e . pytest
python -m pytest tests/ -v
python main.py
```

## Convencion Park

`QleadsD_AphaseToDaxis` (CONFIRMED, M4): fase A alineada con el eje d, q adelanta a d.
`theta_e = nPolePairs * theta_m = 4 * theta_m`.
