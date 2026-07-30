from models.measure_candidate_result import (
    MeasureCandidate,
    MeasureCandidateResult,
)


class MeasureCandidateParser:
    """
    Generates every possible prefix split.

    Example
    -------
    Input:
        cost female patients

    Output:
        cost | female patients
        cost female | patients
        cost female patients |
    """

    @classmethod
    def parse(cls, text: str) -> MeasureCandidateResult:

        text = " ".join(text.split())

        if not text:
            return MeasureCandidateResult(candidates=[])

        words = text.split()

        candidates = []

        for i in range(1, len(words) + 1):

            measure = " ".join(words[:i])

            remaining = " ".join(words[i:])

            candidates.append(
                MeasureCandidate(
                    measure_phrase=measure,
                    remaining_text=remaining,
                )
            )

        print("\n" + "=" * 60)
        print("🔥 MEASURE CANDIDATE PARSER")
        print("Input:", repr(text))
        print()

        for c in candidates:
            print(
                f"Measure: {c.measure_phrase!r:<30}"
                f" Remaining: {c.remaining_text!r}"
            )

        print("=" * 60)

        return MeasureCandidateResult(
            candidates=candidates
        )