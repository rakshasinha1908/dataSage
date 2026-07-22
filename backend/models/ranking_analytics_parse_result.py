from dataclasses import dataclass


@dataclass
class RankingAnalyticsParseResult:
    group_phrase: str | None = None
    measure_phrase: str | None = None
    cleaned_text: str = ""