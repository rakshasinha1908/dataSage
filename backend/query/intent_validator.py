from models.column_schema import ColumnSchema
from models.validation_result import ValidationResult
from models.operation import Operation


class IntentValidator:
    """
    Validates whether a parsed query can be executed.
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
        Operation.COUNT,          # count rows
        Operation.DESCRIBE,
        Operation.COLUMNS,
        Operation.SHOW_ROWS,
    }

    @classmethod
    def validate(
        cls,
        operation,
        matched_columns: list[ColumnSchema],
    ) -> ValidationResult:

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

            return ValidationResult(success=True)

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
                    error=f"'{operation}' can only be applied to numeric columns.",
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