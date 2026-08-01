import re

from models.condition import Condition
from models.numeric_filter_parse_result import (
    NumericFilterParseResult,
)
from query.column_matcher import ColumnMatcher


class NumericFilterParser:
    """
    Extracts numeric comparison filters.

    Examples:

        age > 40
        age >= 40
        cost below 10000
        patients older than 60
    """

    AGE_PATTERNS = [
        (re.compile(r"older than\s+(\d+)", re.IGNORECASE), ">"),
        (re.compile(r"younger than\s+(\d+)", re.IGNORECASE), "<"),
    ]

    PATTERNS = [
        (re.compile(r"(.+?)\s*>=\s*(\d+)", re.IGNORECASE), ">="),
        (re.compile(r"(.+?)\s*<=\s*(\d+)", re.IGNORECASE), "<="),
        (re.compile(r"(.+?)\s*>\s*(\d+)", re.IGNORECASE), ">"),
        (re.compile(r"(.+?)\s*<\s*(\d+)", re.IGNORECASE), "<"),
        (re.compile(r"(.+?)\s*=\s*(\d+)", re.IGNORECASE), "=="),

        (re.compile(r"(.+?)\s+greater than\s+(\d+)", re.IGNORECASE), ">"),
        (re.compile(r"(.+?)\s+above\s+(\d+)", re.IGNORECASE), ">"),
        (re.compile(r"(.+?)\s+over\s+(\d+)", re.IGNORECASE), ">"),

        (re.compile(r"(.+?)\s+less than\s+(\d+)", re.IGNORECASE), "<"),
        (re.compile(r"(.+?)\s+below\s+(\d+)", re.IGNORECASE), "<"),
        (re.compile(r"(.+?)\s+under\s+(\d+)", re.IGNORECASE), "<"),

        (re.compile(r"(.+?)\s+at least\s+(\d+)", re.IGNORECASE), ">="),
        (re.compile(r"(.+?)\s+at most\s+(\d+)", re.IGNORECASE), "<="),

        (re.compile(r"(.+?)\s+equals\s+(\d+)", re.IGNORECASE), "=="),
    ]

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
            match = pattern.search(cleaned_text)
            if not match:
                continue

            age_column = ColumnMatcher.match("age", schema)

            if age_column:
                conditions.append(
                    Condition(
                        column=age_column[0].name,
                        operator=operator,
                        value=int(match.group(1)),
                    )
                )

            cleaned_text = pattern.sub("", cleaned_text, count=1).strip()

        # -----------------------------------
        # Handle general numeric patterns
        # -----------------------------------
        for pattern, operator in cls.PATTERNS:
            match = pattern.search(cleaned_text)
            if not match:
                continue

            column_phrase = match.group(1).strip()
            value = int(match.group(2))

            matched_columns = ColumnMatcher.match(column_phrase, schema)

            if not matched_columns:
                continue

            column = matched_columns[0]

            if not column.is_numeric:
                continue

            conditions.append(
                Condition(
                    column=column.name,
                    operator=operator,
                    value=value,
                )
            )

            cleaned_text = pattern.sub("", cleaned_text, count=1).strip()
            break

        return NumericFilterParseResult(
            conditions=conditions,
            cleaned_text=" ".join(cleaned_text.split()),
        )
