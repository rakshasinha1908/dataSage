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

        return ValidationResult(
            success=True,
            column=matched_columns[0]
        )