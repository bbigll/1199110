"""Validate intended MiniWorld movement against observed feedback."""
from __future__ import annotations

from .directions import direction_from_delta
from .schemas import DirectionValidationResult, MovementResult, NextExplorationAction


class DirectionValidator:
    def validate(self, action: NextExplorationAction, result: MovementResult) -> DirectionValidationResult:
        expected = action.direction.delta
        observed = result.observed_delta
        corrected = direction_from_delta(observed) if observed != (0, 0) else None
        agreement = result.moved and observed == expected
        if agreement:
            score = 1.0
            confidence_delta = 0.1
            reason = "observed movement matched intended direction"
        elif not result.moved and observed == (0, 0):
            score = 0.0
            confidence_delta = -0.2
            reason = "movement was blocked or produced no observed delta"
        else:
            score = 0.25 if corrected is not None else 0.0
            confidence_delta = -0.3
            reason = "observed movement did not match intended direction"
        return DirectionValidationResult(action.direction, expected, observed, result.moved, agreement, score, corrected, confidence_delta, reason)
