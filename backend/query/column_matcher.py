from models.column_schema import ColumnSchema
from utils.text_utils import normalize_text


class ColumnMatcher:
    """
    Matches user text to dataset columns.

    Supports:
    - exact normalized-name matching
    - aliases
    - simple singular/plural normalization
    - word-subset matching
    """

    @staticmethod
    def _normalize_word(word: str) -> str:
        """
        Applies lightweight singular normalization.

        This intentionally avoids aggressive stemming so
        column names are not distorted.
        """

        if len(word) <= 3:
            return word

        # categories -> category
        # cities -> city
        if word.endswith("ies") and len(word) > 4:
            return word[:-3] + "y"

        # classes -> class
        # statuses -> status
        if word.endswith("ses") and len(word) > 4:
            return word[:-2]

        # amounts -> amount
        # customers -> customer
        # products -> product
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]

        return word

    @classmethod
    def _normalize_phrase(cls, text: str) -> str:
        normalized = normalize_text(text)

        words = [
            cls._normalize_word(word)
            for word in normalized.split()
        ]

        return " ".join(words)

    @classmethod
    def match(
        cls,
        text: str,
        schema: list[ColumnSchema],
    ) -> list[ColumnSchema]:
        """
        Returns all matching columns.
        """

        normalized_text = cls._normalize_phrase(text)

        matches: list[ColumnSchema] = []

        # ----------------------------------------
        # Pass 1: Exact match
        # ----------------------------------------

        for column in schema:

            candidate_names = [
                column.normalized_name,
                *column.aliases,
            ]

            for candidate in candidate_names:

                normalized_candidate = (
                    cls._normalize_phrase(candidate)
                )

                if normalized_candidate == normalized_text:
                    matches.append(column)
                    break

        if matches:
            return matches

        # ----------------------------------------
        # Pass 2: Word subset match
        # ----------------------------------------

        text_words = set(
            normalized_text.split()
        )

        if not text_words:
            return []

        for column in schema:

            candidate_names = [
                column.normalized_name,
                *column.aliases,
            ]

            for candidate in candidate_names:

                normalized_candidate = (
                    cls._normalize_phrase(candidate)
                )

                candidate_words = set(
                    normalized_candidate.split()
                )

                if text_words.issubset(candidate_words):
                    matches.append(column)
                    break

        return matches