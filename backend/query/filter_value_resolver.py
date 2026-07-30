from models.condition import Condition
from utils.text_utils import normalize_text


class FilterValueResolver:
    """
    Resolves remaining categorical values into filter conditions.

    Example
    -------
    Remaining Text:
        "female patients"

    Output:
        Condition(column="Gender", operator="==", value="Female")
    """

    @classmethod
    def resolve(
        cls,
        text: str,
        schema,
    ):
        normalized_text = normalize_text(text)

        conditions = []

        for column in schema:

            for sample_value in column.sample_values:

                if not isinstance(sample_value, str):
                    continue

                normalized_value = normalize_text(sample_value)

                if normalized_value not in normalized_text:
                    continue

                conditions.append(
                    Condition(
                        column=column.name,
                        operator="==",
                        value=sample_value,
                    )
                )

                normalized_text = normalized_text.replace(
                    normalized_value,
                    "",
                    1,
                )

        cleaned_text = " ".join(normalized_text.split())

        return conditions, cleaned_text