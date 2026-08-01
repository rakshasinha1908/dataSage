import re

from models.condition import Condition
from models.numeric_filter_parse_result import (
    NumericFilterParseResult,
)
from query.column_matcher import ColumnMatcher


class NumericFilterParser:
    """
    Extracts numeric comparison filters.

    Supported examples:

        age > 40
        age >= 40
        cost below 10000
        satisfaction at least 4

        age > 40 and satisfaction >= 4
        age >= 30 and age <= 50

        older than 60
        younger than 30

    Numeric conditions may also contain leading non-column words:

        patients age > 50
        records total cost > 1000

    In those cases, numeric column resolution progressively checks
    suffixes of the phrase while preferring the longest valid match.
    """

    # -----------------------------------
    # Age-specific natural language
    # -----------------------------------

    AGE_PATTERNS = [
        (
            re.compile(
                r"\bolder than\s+(-?\d+(?:\.\d+)?)\b",
                re.IGNORECASE,
            ),
            ">",
        ),
        (
            re.compile(
                r"\byounger than\s+(-?\d+(?:\.\d+)?)\b",
                re.IGNORECASE,
            ),
            "<",
        ),
    ]

    # -----------------------------------
    # General numeric comparisons
    # -----------------------------------

    PATTERNS = [
        (
            re.compile(
                r"(.+?)\s*>=\s*(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">=",
        ),
        (
            re.compile(
                r"(.+?)\s*<=\s*(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<=",
        ),
        (
            re.compile(
                r"(.+?)\s*>\s*(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">",
        ),
        (
            re.compile(
                r"(.+?)\s*<\s*(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<",
        ),
        (
            re.compile(
                r"(.+?)\s*=\s*(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "==",
        ),
        (
            re.compile(
                r"(.+?)\s+greater than\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">",
        ),
        (
            re.compile(
                r"(.+?)\s+above\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">",
        ),
        (
            re.compile(
                r"(.+?)\s+over\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">",
        ),
        (
            re.compile(
                r"(.+?)\s+less than\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<",
        ),
        (
            re.compile(
                r"(.+?)\s+below\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<",
        ),
        (
            re.compile(
                r"(.+?)\s+under\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<",
        ),
        (
            re.compile(
                r"(.+?)\s+at least\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            ">=",
        ),
        (
            re.compile(
                r"(.+?)\s+at most\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "<=",
        ),
        (
            re.compile(
                r"(.+?)\s+equals\s+(-?\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "==",
        ),
    ]

    @staticmethod
    def _convert_number(value: str):
        """
        Convert numeric text into int or float.

        Examples:
            "40"   -> 40
            "40.5" -> 40.5
            "-10"  -> -10
        """

        number = float(value)

        if number.is_integer():
            return int(number)

        return number

    @classmethod
    def _resolve_numeric_column(
        cls,
        column_phrase: str,
        schema,
    ):
        """
        Resolve a numeric column from a phrase.

        The full phrase is attempted first.

        If it does not resolve, progressively shorter suffixes are
        checked. This allows harmless leading words to remain in the
        query without preventing numeric-filter extraction.

        Example:

            "patients age"

        tries:

            "patients age"
            "age"

        The longest successful numeric match wins.

        This remains dataset-agnostic because no domain-specific
        vocabulary is removed or hardcoded here.
        """

        words = column_phrase.split()

        for start_index in range(len(words)):
            candidate_phrase = " ".join(
                words[start_index:]
            ).strip()

            if not candidate_phrase:
                continue

            matched_columns = ColumnMatcher.match(
                candidate_phrase,
                schema,
            )

            if not matched_columns:
                continue

            for column in matched_columns:
                if column.is_numeric:
                    return column

        return None

    @classmethod
    def parse(
        cls,
        text: str,
        schema,
    ):
        conditions = []
        cleaned_text = text

        # -----------------------------------
        # Handle age-specific patterns
        # -----------------------------------

        for pattern, operator in cls.AGE_PATTERNS:

            while True:

                match = pattern.search(cleaned_text)

                if not match:
                    break

                age_columns = ColumnMatcher.match(
                    "age",
                    schema,
                )

                if age_columns and age_columns[0].is_numeric:

                    conditions.append(
                        Condition(
                            column=age_columns[0].name,
                            operator=operator,
                            value=cls._convert_number(
                                match.group(1)
                            ),
                        )
                    )

                cleaned_text = (
                    cleaned_text[:match.start()]
                    + " "
                    + cleaned_text[match.end():]
                )

                cleaned_text = " ".join(
                    cleaned_text.split()
                )

        # -----------------------------------
        # Split potential numeric conditions
        #
        # Example:
        #
        # patients age > 50 and satisfaction >= 4
        #
        # becomes:
        #
        # [
        #   "patients age > 50",
        #   "satisfaction >= 4"
        # ]
        # -----------------------------------

        clauses = re.split(
            r"\s+\band\b\s+",
            cleaned_text,
            flags=re.IGNORECASE,
        )

        remaining_clauses = []

        # -----------------------------------
        # Parse every clause independently
        # -----------------------------------

        for clause in clauses:

            clause = clause.strip()

            if not clause:
                continue

            matched_condition = False

            for pattern, operator in cls.PATTERNS:

                match = pattern.fullmatch(clause)

                if not match:
                    continue

                column_phrase = match.group(1).strip()

                value = cls._convert_number(
                    match.group(2)
                )

                column = cls._resolve_numeric_column(
                    column_phrase,
                    schema,
                )

                if column is None:
                    continue

                conditions.append(
                    Condition(
                        column=column.name,
                        operator=operator,
                        value=value,
                    )
                )

                matched_condition = True
                break

            if not matched_condition:
                remaining_clauses.append(clause)

        cleaned_text = " ".join(
            remaining_clauses
        )

        cleaned_text = " ".join(
            cleaned_text.split()
        )

        return NumericFilterParseResult(
            conditions=conditions,
            cleaned_text=cleaned_text,
        )
