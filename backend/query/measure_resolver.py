from models.column_schema import ColumnSchema
from query.column_matcher import ColumnMatcher
from models.measure_candidate_result import (
    MeasureCandidateResult,
)


class MeasureResolver:

    @classmethod
    def resolve(
        cls,
        candidate_result: MeasureCandidateResult,
        schema: list[ColumnSchema],
    ):

        for candidate in candidate_result.candidates:

            matches = ColumnMatcher.match(
                candidate.measure_phrase,
                schema,
            )

            if matches:

                return matches[0], candidate.remaining_text

        return None, candidate_result.candidates[-1].remaining_text if candidate_result.candidates else ""