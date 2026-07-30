from dataclasses import dataclass


@dataclass
class MeasureCandidate:
    """
    One possible interpretation of the measure phrase.
    """

    measure_phrase: str
    remaining_text: str


@dataclass
class MeasureCandidateResult:
    """
    Output of MeasureCandidateParser.
    """

    candidates: list[MeasureCandidate]