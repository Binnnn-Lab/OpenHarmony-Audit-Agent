"""Evidence normalisation, persistence and decision gates."""

from .decision_gate import evaluate_candidate
from .normalizer import findings_from_sarif

__all__ = ["evaluate_candidate", "findings_from_sarif"]

