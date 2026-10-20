"""Evidence taxonomy and decision vocabulary."""

EVIDENCE_KINDS = {
    "source_review",
    "deterministic_verification",
    "poc_execution",
    "decisive_counterevidence",
    "static_path",
    "sarif_alert",
    "ql_patch",
    "function_sanitizer",
    "symbolic_reachability",
    "history",
    "fp_experience",
    "blind_verification",
    "poc_plan",
    "repair_plan",
    "model_reasoning",
}

DECISION_VERDICTS = {"CONFIRMED", "STATIC_ONLY", "REJECTED", "NEEDS_EVIDENCE"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}

