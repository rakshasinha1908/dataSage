import re

from models.column_schema import ColumnSchema
from models.validation_result import ValidationResult
from models.operation import Operation


class IntentValidator:
    """
    Validates whether a parsed query can be executed safely.

    Validation is intentionally conservative:
    if meaningful query text remains unresolved, DataSage
    should fail rather than silently execute a different query.
    """

    # -------------------------------
    # Operations that require a target column.
    # -------------------------------
    COLUMN_OPERATIONS = {
        Operation.MEAN,
        Operation.SUM,
        Operation.MIN,
        Operation.MAX,
    }

    # -------------------------------
    # Operations that work on the dataset
    # and do not require a target column.
    # -------------------------------
    DATASET_OPERATIONS = {
        Operation.HEAD,
        Operation.TAIL,
        Operation.COUNT,
        Operation.DESCRIBE,
        Operation.COLUMNS,
        Operation.SHOW_ROWS,
    }

    # -------------------------------
    # Filter syntax that should have been
    # consumed during query understanding.
    # -------------------------------
    UNRESOLVED_FILTER_PATTERN = re.compile(
        r"""
        >=
        |<=
        |>
        |<
        |=
        |\bgreater\s+than\b
        |\babove\b
        |\bover\b
        |\bless\s+than\b
        |\bbelow\b
        |\bunder\b
        |\bat\s+least\b
        |\bat\s+most\b
        |\bequals\b
        |\bis\b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def _clean_unresolved_text(
        cls,
        unresolved_text: str,
    ) -> str:
        """
        Normalize unresolved text before validation.
        """

        if not unresolved_text:
            return ""

        return " ".join(
            unresolved_text.lower().split()
        )

    @classmethod
    def _has_unresolved_filter(
        cls,
        unresolved_text: str,
    ) -> bool:
        """
        Returns True when unresolved text still contains
        recognizable filter/comparison syntax.
        """

        if not unresolved_text:
            return False

        return bool(
            cls.UNRESOLVED_FILTER_PATTERN.search(
                unresolved_text
            )
        )

    @classmethod
    def validate(
        cls,
        operation,
        matched_columns: list[ColumnSchema],
        unresolved_text: str = "",
    ) -> ValidationResult:

        unresolved_text = cls._clean_unresolved_text(
            unresolved_text
        )

        # =================================================
        # Unresolved filter syntax
        # =================================================

        if cls._has_unresolved_filter(
            unresolved_text
        ):
            return ValidationResult(
                success=False,
                error=(
                    "I couldn't understand part of the requested "
                    "filter. Please check the column name or "
                    "filter value."
                ),
            )

        # =================================================
        # COUNT
        # =================================================
        #
        # COUNT is especially dangerous because executing
        # it with ignored text silently returns the total
        # number of rows.
        #
        # Example:
        #
        #     count female customers
        #
        # If "female" cannot be resolved, executing COUNT
        # would incorrectly return the full dataset size.
        #
        # Therefore unresolved text is not allowed here.
        # =================================================

        if operation == Operation.COUNT:

            if unresolved_text:
                return ValidationResult(
                    success=False,
                    error=(
                        "I couldn't understand part of the "
                        "request. Please check the column name "
                        "or filter value."
                    ),
                )

            if matched_columns:
                return ValidationResult(
                    success=True,
                    column=matched_columns[0],
                )

            return ValidationResult(
                success=True
            )

        # =================================================
        # Other dataset operations
        # =================================================

        if operation in cls.DATASET_OPERATIONS:
            return ValidationResult(
                success=True
            )

        # =================================================
        # Column operations
        # =================================================

        if operation in cls.COLUMN_OPERATIONS:

            if not matched_columns:
                return ValidationResult(
                    success=False,
                    error="No matching column found.",
                )

            column = matched_columns[0]

            if (
                operation in {
                    Operation.MEAN,
                    Operation.SUM,
                }
                and not column.is_numeric
            ):
                return ValidationResult(
                    success=False,
                    error=(
                        f"'{operation}' can only be applied "
                        "to numeric columns."
                    ),
                )

            return ValidationResult(
                success=True,
                column=column,
            )

        # =================================================
        # Default
        # =================================================

        if not matched_columns:
            return ValidationResult(
                success=False,
                error="No matching column found.",
            )

        return ValidationResult(
            success=True,
            column=matched_columns[0],
        )