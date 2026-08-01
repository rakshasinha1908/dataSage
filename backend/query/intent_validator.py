import re

from models.column_schema import ColumnSchema
from models.validation_result import ValidationResult
from models.operation import Operation


class IntentValidator:
    """
    Validates whether a parsed query can be executed safely.
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
    #
    # If it remains afterward, the user likely
    # attempted a filter that DataSage could not
    # resolve safely.
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
    def _has_unresolved_filter(
        cls,
        unresolved_text: str,
    ) -> bool:
        """
        Return True when unresolved text still contains
        recognizable filter/comparison syntax.

        Harmless residual words such as "patients" or
        "records" are not treated as errors.
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

        # -------------------------------
        # Unresolved filter validation
        # -------------------------------
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

        # -------------------------------
        # Dataset Operations
        # -------------------------------
        if operation in cls.DATASET_OPERATIONS:

            # COUNT can optionally work on a column
            if (
                operation == Operation.COUNT
                and matched_columns
            ):
                return ValidationResult(
                    success=True,
                    column=matched_columns[0],
                )

            return ValidationResult(
                success=True
            )

        # -------------------------------
        # Column Operations
        # -------------------------------
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

        # -------------------------------
        # Default
        # -------------------------------
        if not matched_columns:
            return ValidationResult(
                success=False,
                error="No matching column found.",
            )

        return ValidationResult(
            success=True,
            column=matched_columns[0],
        )