#!/usr/bin/env python3
"""
J3.2 — Protocolo reproducible para generación de etiquetas ANFIS.

Versión: 0.2

Propósito
---------
Congelar el criterio metodológico utilizado posteriormente para generar
las etiquetas de adaptación de Kp y Ki.

La arquitectura ANFIS definida es:

    z = [error_w, delta_error_w, abs_iq]
        ->
    [Kp_adapt, Ki_adapt]

J3.2 NO genera etiquetas y NO entrena ANFIS.

Las etiquetas serán generadas posteriormente mediante una evaluación
contrafactual de las configuraciones candidatas obtenidas en J3.1.

Principio de trazabilidad
-------------------------
B2.5 -> J3.1 -> J3.2 -> J3.3 -> J3.4 -> entrenamiento ANFIS

B2.5:
    exploración de sensibilidad.

J3.1:
    catálogo multicriterio de configuraciones candidatas.

J3.2:
    definición del criterio de etiquetado.

J3.3:
    generación del dataset temporal y etiquetas.

J3.4:
    validación de las etiquetas antes del entrenamiento.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

J31_DIR = ROOT / "experiments" / "j3_1_label_criteria"
J31_CATALOG = J31_DIR / "j3_1_configuration_catalog.csv"

OUTPUT_DIR = ROOT / "experiments" / "j3_2_label_criteria"
PROTOCOL_CSV = OUTPUT_DIR / "j3_2_protocol_summary.csv"


# ============================================================================
# IDENTIFICACIÓN
# ============================================================================

PROTOCOL_ID = "J3.2"
PROTOCOL_VERSION = "0.2"
STATUS = "FROZEN"


# ============================================================================
# ARQUITECTURA ANFIS
# ============================================================================

ANFIS_INPUTS = [
    "error_w",
    "delta_error_w",
    "abs_iq",
]

ANFIS_OUTPUTS = [
    "kp_adapt",
    "ki_adapt",
]


# ============================================================================
# METADATOS EXPERIMENTALES
# ============================================================================

METADATA_FIELDS = [
    "scenario",
    "transition",
]

METADATA_ROLE = (
    "Los metadatos experimentales se conservan para trazabilidad y "
    "análisis, pero no forman parte de las entradas ANFIS."
)


# ============================================================================
# DATOS TEMPORALES REQUERIDOS
# ============================================================================

TEMPORAL_REQUIRED_FIELDS = [
    "t",
    "scenario",
    "transition",
    "kp_factor",
    "ki_factor",
    "kp",
    "ki",
    "omega_ref",
    "omega_m",
    "error_w",
    "delta_error_w",
    "iq",
    "iq_ref",
    "te",
]


# ============================================================================
# RESTRICCIÓN DE CORRIENTE
# ============================================================================

PHYSICAL_CURRENT_LIMIT_A = 79.5
CONTROLLER_IQ_REF_LIMIT_A = 112.43

CURRENT_FEASIBILITY_RULE = (
    "Una configuración es físicamente factible si la corriente medida "
    "max(|iq|) durante la ventana de evaluación no supera 79.5 A."
)

CURRENT_REFERENCE_RULE = (
    "iq_ref representa la referencia generada por el lazo de velocidad "
    "y no se considera equivalente a la corriente física del motor."
)


# ============================================================================
# CONJUNTO DE GANANCIAS CANDIDATAS
# ============================================================================

KP_BASE = 5.2804
KI_BASE = 1.2693

KP_FACTOR_MIN = 0.50
KP_FACTOR_MAX = 2.00

KI_FACTOR_MIN = 0.50
KI_FACTOR_MAX = 2.00

KP_MIN = KP_BASE * KP_FACTOR_MIN
KP_MAX = KP_BASE * KP_FACTOR_MAX

KI_MIN = KI_BASE * KI_FACTOR_MIN
KI_MAX = KI_BASE * KI_FACTOR_MAX

GAIN_CANDIDATE_RULE = (
    "Las etiquetas J3.3 se generan únicamente a partir de las "
    "configuraciones candidatas discretas del barrido J3.1."
)


# ============================================================================
# VENTANA TEMPORAL
# ============================================================================

WINDOW_DURATION_S = 0.010

WINDOW_RULE = (
    "La evaluación local se realiza sobre una ventana temporal de "
    "10 ms asociada al estado observable. La ventana se utiliza como "
    "decisión metodológica y no se interpreta como una constante física "
    "del motor."
)


# ============================================================================
# CRITERIO DE SELECCIÓN
# ============================================================================

SELECTION_METHOD = "LEXICOGRAPHIC"

SELECTION_STAGES = [
    "1. Factibilidad de corriente física.",
    "2. Mínimo MAE de velocidad.",
    "3. Mínimo esfuerzo asociado a iq_ref en caso de equivalencia.",
    "4. Estado ambiguo si persiste la equivalencia.",
]

ERROR_METRIC = "MAE"

ERROR_DEFINITION = (
    "J_error = mean(abs(error_w)) dentro de la ventana de evaluación."
)

CURRENT_REFERENCE_METRIC = "MEAN_ABS_IQ_REF"

CURRENT_REFERENCE_DEFINITION = (
    "J_current_reference = mean(abs(iq_ref)) dentro de la ventana "
    "de evaluación."
)


# ============================================================================
# TOLERANCIAS DE EQUIVALENCIA
# ============================================================================

ERROR_TOLERANCE_STATUS = "DEFINED_RELATIVE"

ERROR_RELATIVE_TOLERANCE = 0.01

ERROR_TOLERANCE_RULE = (
    "Dos configuraciones se consideran equivalentes respecto al MAE "
    "si la diferencia relativa entre sus valores es <= 1 % respecto "
    "al menor MAE positivo."
)

AMBIGUITY_RULE = (
    "Si después del criterio secundario permanecen varias candidatas "
    "indistinguibles, no se fuerza una etiqueta y el estado se marca "
    "como AMBIGUOUS."
)


# ============================================================================
# ESTADO DE ETIQUETADO
# ============================================================================

LABEL_STATUS = "NOT_GENERATED"

AMBIGUOUS_LABEL_STATUS = "NO_LABEL"

TRAINING_STATUS = "NOT_STARTED"


# ============================================================================
# PROCEDENCIA
# ============================================================================

SOURCE_CHAIN = (
    "B2.5 -> J3.1 -> J3.2 -> J3.3 -> J3.4 -> entrenamiento ANFIS"
)

B25_ROLE = (
    "B2.5 proporciona la exploración de sensibilidad y las métricas "
    "de las configuraciones evaluadas."
)

J31_ROLE = (
    "J3.1 proporciona el catálogo reproducible de configuraciones "
    "candidatas. No proporciona directamente etiquetas estado->ganancia."
)

J32_ROLE = (
    "J3.2 define cómo una configuración candidata puede convertirse "
    "en etiqueta para un estado observable."
)


def load_j31_catalog() -> list[dict[str, str]]:
    """Carga el catálogo J3.1 únicamente para verificar procedencia."""
    if not J31_CATALOG.exists():
        raise FileNotFoundError(
            f"No existe el catálogo J3.1 esperado: {J31_CATALOG}"
        )

    with J31_CATALOG.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError("El catálogo J3.1 está vacío.")

    required = {"kp_factor", "ki_factor", "kp", "ki"}
    missing = required - set(rows[0].keys())

    if missing:
        raise RuntimeError(
            "El catálogo J3.1 no contiene las columnas requeridas: "
            + ", ".join(sorted(missing))
        )

    return rows


def build_protocol_rows(catalog: list[dict[str, str]]) -> list[dict[str, str]]:
    """Construye el resumen auditable del protocolo J3.2."""
    unique_candidates = sorted(
        {
            (
                row["kp_factor"],
                row["ki_factor"],
                row["kp"],
                row["ki"],
            )
            for row in catalog
        }
    )

    rows = [
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "status",
            "item": "status",
            "value": STATUS,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "architecture",
            "item": "anfis_inputs",
            "value": ", ".join(ANFIS_INPUTS),
            "source": "architecture",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "architecture",
            "item": "anfis_outputs",
            "value": ", ".join(ANFIS_OUTPUTS),
            "source": "architecture",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "metadata",
            "item": "metadata_fields",
            "value": ", ".join(METADATA_FIELDS),
            "source": "experimental_traceability",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "metadata",
            "item": "metadata_role",
            "value": METADATA_ROLE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "current",
            "item": "physical_current_limit_A",
            "value": str(PHYSICAL_CURRENT_LIMIT_A),
            "source": "M4/documented motor limit",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "current",
            "item": "controller_iq_ref_limit_A",
            "value": str(CONTROLLER_IQ_REF_LIMIT_A),
            "source": "speed_controller",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "current",
            "item": "physical_feasibility_rule",
            "value": CURRENT_FEASIBILITY_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "current",
            "item": "iq_ref_semantics",
            "value": CURRENT_REFERENCE_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "gains",
            "item": "kp_base",
            "value": str(KP_BASE),
            "source": "speed_controller",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "gains",
            "item": "ki_base",
            "value": str(KI_BASE),
            "source": "speed_controller",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "gains",
            "item": "kp_range",
            "value": f"[{KP_MIN:.7f}, {KP_MAX:.7f}]",
            "source": "J3.1 candidate envelope",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "gains",
            "item": "ki_range",
            "value": f"[{KI_MIN:.7f}, {KI_MAX:.7f}]",
            "source": "J3.1 candidate envelope",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "gains",
            "item": "candidate_rule",
            "value": GAIN_CANDIDATE_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "temporal",
            "item": "window_duration_s",
            "value": str(WINDOW_DURATION_S),
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "temporal",
            "item": "window_rule",
            "value": WINDOW_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "selection_method",
            "value": SELECTION_METHOD,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "selection_stages",
            "value": " | ".join(SELECTION_STAGES),
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "error_metric",
            "value": ERROR_METRIC,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "error_definition",
            "value": ERROR_DEFINITION,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "current_reference_metric",
            "value": CURRENT_REFERENCE_METRIC,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "current_reference_definition",
            "value": CURRENT_REFERENCE_DEFINITION,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "error_tolerance",
            "value": f"{ERROR_RELATIVE_TOLERANCE:.4f}",
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "error_tolerance_rule",
            "value": ERROR_TOLERANCE_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "selection",
            "item": "ambiguity_rule",
            "value": AMBIGUITY_RULE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "labeling",
            "item": "label_status",
            "value": LABEL_STATUS,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "labeling",
            "item": "ambiguous_label_status",
            "value": AMBIGUOUS_LABEL_STATUS,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "training",
            "item": "training_status",
            "value": TRAINING_STATUS,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "dataset",
            "item": "required_temporal_fields",
            "value": ", ".join(TEMPORAL_REQUIRED_FIELDS),
            "source": "J3.3 requirement",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "provenance",
            "item": "source_chain",
            "value": SOURCE_CHAIN,
            "source": "project workflow",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "provenance",
            "item": "B2_5_role",
            "value": B25_ROLE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "provenance",
            "item": "J3_1_role",
            "value": J31_ROLE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "provenance",
            "item": "J3_2_role",
            "value": J32_ROLE,
            "source": "J3.2",
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "catalog",
            "item": "J3_1_catalog_rows",
            "value": str(len(catalog)),
            "source": str(J31_CATALOG.relative_to(ROOT)),
        },
        {
            "protocol": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "section": "catalog",
            "item": "unique_candidates",
            "value": str(len(unique_candidates)),
            "source": str(J31_CATALOG.relative_to(ROOT)),
        },
    ]

    return rows


def write_protocol(rows: list[dict[str, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "protocol",
        "version",
        "section",
        "item",
        "value",
        "source",
    ]

    with PROTOCOL_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    print("=" * 72)
    print(" J3.2 — LABEL PROTOCOL v0.2")
    print("=" * 72)

    catalog = load_j31_catalog()
    rows = build_protocol_rows(catalog)
    write_protocol(rows)

    unique_candidates = {
        (
            row["kp_factor"],
            row["ki_factor"],
            row["kp"],
            row["ki"],
        )
        for row in catalog
    }

    print(f"Status            : {STATUS}")
    print(f"J3.1 catalog rows : {len(catalog)}")
    print(f"Unique candidates : {len(unique_candidates)}")
    print(f"Kp range          : [{KP_MIN:.7f}, {KP_MAX:.7f}]")
    print(f"Ki range          : [{KI_MIN:.7f}, {KI_MAX:.7f}]")
    print(f"Window            : {WINDOW_DURATION_S:.3f} s")
    print(f"Selection         : {SELECTION_METHOD}")
    print(f"Error metric      : {ERROR_METRIC}")
    print(f"Error tolerance   : {ERROR_RELATIVE_TOLERANCE:.2%}")
    print(f"Current limit     : {PHYSICAL_CURRENT_LIMIT_A:.2f} A")
    print(f"Labels generated  : {LABEL_STATUS}")
    print(f"Training started  : {TRAINING_STATUS}")
    print()
    print(f"Protocol written  : {PROTOCOL_CSV}")
    print("=" * 72)


if __name__ == "__main__":
    main()
