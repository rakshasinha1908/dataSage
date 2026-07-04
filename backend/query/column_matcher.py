from models.column_schema import ColumnSchema
from utils.text_utils import normalize_text


class ColumnMatcher:
    """
    Matches user text to dataset columns.
    """

    @classmethod
    def match(
        cls,
        text: str,
        schema: list[ColumnSchema],
    ) -> list[ColumnSchema]:
        """
        Returns all matching columns.
        """

        normalized_text = normalize_text(text)

        matches: list[ColumnSchema] = []

        # -------------------------------
        # Pass 1 : Exact match
        # -------------------------------

        for column in schema:

            if column.normalized_name == normalized_text:
                matches.append(column)

        if matches:
            return matches

        # -------------------------------
        # Pass 2 : Word subset match
        # -------------------------------

        text_words = set(normalized_text.split())

        for column in schema:

            column_words = set(column.normalized_name.split())

            if text_words.issubset(column_words):
                matches.append(column)

        return matches