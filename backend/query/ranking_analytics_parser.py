import re

from models.ranking_analytics_parse_result import (
    RankingAnalyticsParseResult,
)


class RankingAnalyticsParser:
    """
    Parses ranking analytics queries.

    Supported structures
    --------------------

    Explicit "by" structure:

        categories by transaction amount

        group_phrase   -> categories
        measure_phrase -> transaction amount


    Natural ranking structure:

        which category has the highest average transaction amount

        group_phrase   -> category
        measure_phrase -> transaction amount

    The parser only identifies linguistic structure.
    Actual column resolution remains the responsibility
    of QueryUnderstanding / ColumnMatcher.
    """

    # -------------------------------------------------
    # Explicit grouping
    #
    # Example:
    #   categories by transaction amount
    # -------------------------------------------------

    BY_PATTERN = re.compile(
        r"^(.*?)\s+by(?:\s+(.*))?$",
        re.IGNORECASE,
    )

    # -------------------------------------------------
    # Natural ranking question
    #
    # Examples:
    #
    #   which cartoon has the highest viewing time
    #   which city has highest average sales
    #   what category has the lowest average cost
    #
    # RankingParser / OperationParser may already have
    # removed some ranking / operation language, so the
    # pattern deliberately keeps the middle flexible.
    # -------------------------------------------------

    NATURAL_PATTERN = re.compile(
        r"""
        ^(?:which|what)\s+
        (?P<group>.+?)
        \s+(?:has|have|had)\s+
        (?:
            (?:the\s+)?
            (?:highest|lowest|maximum|minimum|top|bottom)
            \s*
        )?
        (?:
            average|mean|total|sum|count|minimum|maximum
        )?
        \s*
        (?P<measure>.+)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def parse(
        cls,
        text: str,
    ) -> RankingAnalyticsParseResult:

        text = " ".join(text.split())

        # ---------------------------------------------
        # Form 1:
        # categories by transaction amount
        # ---------------------------------------------

        match = cls.BY_PATTERN.match(text)

        if match:
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

        # ---------------------------------------------
        # Form 2:
        # which category has the highest average cost
        # ---------------------------------------------

        match = cls.NATURAL_PATTERN.match(text)

        if match:
            group_phrase = (
                match.group("group").strip()
            )

            measure_phrase = (
                match.group("measure").strip()
            )

            return RankingAnalyticsParseResult(
                group_phrase=group_phrase,
                measure_phrase=measure_phrase,
                cleaned_text="",
            )

        # ---------------------------------------------
        # No ranking-analytics structure understood
        # ---------------------------------------------

        return RankingAnalyticsParseResult(
            cleaned_text=text,
        )