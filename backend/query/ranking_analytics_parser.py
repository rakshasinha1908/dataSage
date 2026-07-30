import re

from models.ranking_analytics_parse_result import (
    RankingAnalyticsParseResult,
)


class RankingAnalyticsParser:
    """
    Parses ranking analytics queries.

    Example:

        Top 5 categories by transaction amount

    group_phrase   -> categories
    measure_phrase -> transaction amount
    """

    PATTERN = re.compile(
        r"^(.*?)\s+by(?:\s+(.*))?$",
        re.IGNORECASE,
    )

    @classmethod
    def parse(
        cls,
        text: str,
    ):

        match = cls.PATTERN.match(text)

        if not match:
            return RankingAnalyticsParseResult(
                cleaned_text=text,
            )

        group_phrase = match.group(1).strip()
        measure_phrase = (
            match.group(2).strip()
            if match.group(2)
            else ""
        )

        return RankingAnalyticsParseResult(
            group_phrase=group_phrase,
            measure_phrase=measure_phrase,
            cleaned_text="",
        )