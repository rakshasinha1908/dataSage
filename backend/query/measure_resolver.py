from models.column_schema import ColumnSchema
from query.column_matcher import ColumnMatcher
from models.measure_candidate_result import (
    MeasureCandidateResult,
)


class MeasureResolver:
    """
    Resolves measure candidates against the dataset schema.

    If a measure is found:
        returns (matched_column, remaining_text)

    If no measure is found:
        preserves the original input text so downstream
        parsers can still extract dimensions and filters.
    """

    @classmethod
    def resolve(
        cls,
        candidate_result: MeasureCandidateResult,
        schema: list[ColumnSchema],
    ):

        # ----------------------------------------
        # Try candidates from shortest prefix
        # to longest prefix
        # ----------------------------------------
        for candidate in candidate_result.candidates:

            matches = ColumnMatcher.match(
                candidate.measure_phrase,
                schema,
            )

            if matches:
                return (
                    matches[0],
                    candidate.remaining_text,
                )

        # ----------------------------------------
        # No measure matched
        # ----------------------------------------
        if not candidate_result.candidates:
            return None, ""

        # Reconstruct the original input.
        #
        # The first candidate always represents:
        #
        # first word | everything else
        #
        # Therefore combining them gives us the
        # original text without losing filters.
        first_candidate = candidate_result.candidates[0]

        original_text = " ".join(
            part
            for part in (
                first_candidate.measure_phrase,
                first_candidate.remaining_text,
            )
            if part
        )

        return None, original_text