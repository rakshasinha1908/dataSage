from models.column_schema import ColumnSchema
from models.validation_result import ValidationResult


class IntentValidator:
    """
    Validates whether a parsed query can be executed.
    """

    @classmethod
    def validate(
        cls,
        operation: str,
        matched_columns: list[ColumnSchema],
    ) -> ValidationResult:

        # Rule 1:
        # No matching columns
        if not matched_columns:
            return ValidationResult(
                success=False,
                error="No matching column found."
            )

        column = matched_columns[0]

        # Rule 2:
        # Mean and Sum require numeric columns.
        if operation in ("mean", "sum"):
            if not column.is_numeric:
                return ValidationResult(
                    success=False,
                    error=f"'{operation}' can only be applied to numeric columns."
                )

        return ValidationResult(
            success=True,
            column=column
        )
