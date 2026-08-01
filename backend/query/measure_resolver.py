from models.column_schema import ColumnSchema
from query.column_matcher import ColumnMatcher
from models.measure_candidate_result import (
    MeasureCandidateResult,
)

from utils.text_utils import normalize_text


class MeasureResolver:
    """
    Resolves analytical measure candidates against
    the dataset schema.

    Resolution strategy
    -------------------
    1. Prefer exact matches against column names / aliases.
    2. Among exact matches, prefer the longest phrase.
    3. Fall back to the generic ColumnMatcher only when
       no exact candidate exists.
    4. Preserve the original text when no measure resolves.

    This prevents short ambiguous prefixes from consuming
    only part of a multi-word analytical measure.
    """

    @classmethod
    def resolve(
        cls,
        candidate_result: MeasureCandidateResult,
        schema: list[ColumnSchema],
    ):

        candidates = candidate_result.candidates

        # ----------------------------------------
        # No candidates
        # ----------------------------------------
        if not candidates:
            return None, ""

        # ========================================
        # PASS 1
        # Exact schema / alias matches
        # ========================================
        #
        # Search longest candidate first.
        #
        # Example:
        #
        # transaction amounts
        #
        # should resolve as the complete measure
        # rather than resolving "transaction"
        # prematurely.
        # ========================================

        for candidate in reversed(candidates):

            normalized_phrase = normalize_text(
                candidate.measure_phrase
            )

            for column in schema:

                candidate_names = {
                    normalize_text(column.normalized_name),
                    *[
                        normalize_text(alias)
                        for alias in column.aliases
                    ],
                }

                if normalized_phrase in candidate_names:
                    return (
                        column,
                        candidate.remaining_text,
                    )

        # ========================================
        # PASS 2
        # Generic matcher fallback
        # ========================================
        #
        # Keep the existing flexible matching
        # behaviour, but only after exact aliases
        # have been exhausted.
        # ========================================

        for candidate in candidates:

            matches = ColumnMatcher.match(
                candidate.measure_phrase,
                schema,
            )

            if matches:
                return (
                    matches[0],
                    candidate.remaining_text,
                )

        # ========================================
        # No measure matched
        # ========================================

        first_candidate = candidates[0]

        original_text = " ".join(
            part
            for part in (
                first_candidate.measure_phrase,
                first_candidate.remaining_text,
            )
            if part
        )

        return None, original_text