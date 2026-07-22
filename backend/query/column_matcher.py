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

        print("\n" + "=" * 70)
        print("Input:", text)
        print("Normalized:", normalized_text)
        print("Available Columns:")

        for column in schema:
            print(
                f"  {column.name} -> {[column.normalized_name, *column.aliases]}"
            )

        print("=" * 70)

        matches: list[ColumnSchema] = []

        # -------------------------------
        # Pass 1 : Exact match
        # -------------------------------

        print("\nPASS 1 : Exact Match")

        for column in schema:

            candidate_names = [
                column.normalized_name,
                *column.aliases,
            ]

            for candidate in candidate_names:

                print(
                    f"Comparing '{normalized_text}' == '{candidate}'"
                )

                if candidate == normalized_text:
                    print("✅ Exact Match:", column.name)
                    matches.append(column)
                    break

        if matches:
            print("Returning:", [c.name for c in matches])
            return matches

        # -------------------------------
        # Pass 2 : Word subset match
        # -------------------------------

        print("\nPASS 2 : Word Subset Match")

        text_words = set(normalized_text.split())

        print("Text Words:", text_words)

        for column in schema:

            candidate_names = [
                column.normalized_name,
                *column.aliases,
            ]

            for candidate in candidate_names:

                candidate_words = set(candidate.split())

                print(
                    f"{text_words} ⊆ {candidate_words} -> {text_words.issubset(candidate_words)}"
                )

                if text_words.issubset(candidate_words):
                    print("✅ Subset Match:", column.name)
                    matches.append(column)
                    break

        if matches:
            print("Returning:", [c.name for c in matches])
            return matches

        print("❌ No Column Matched")
        print("=" * 70 + "\n")

        return []