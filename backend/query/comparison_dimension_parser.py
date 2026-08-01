from models.dimension import Dimension
from models.dimension_parse_result import DimensionParseResult
from query.column_matcher import ColumnMatcher
from utils.text_utils import normalize_text


class ComparisonDimensionParser:
    """
    Resolves implicit grouping dimensions from comparative language.

    Comparison intent is detected from the original question,
    while dimension evidence is resolved from the remaining
    analytical text.

    Examples
    --------
    compare between members and non members
    compare male and female patients
    difference between prepaid and non prepaid orders
    subscribers and non subscribers

    Resolution remains schema-driven and does not contain
    dataset-specific column mappings.
    """

    COMPARISON_MARKERS = {
        "compare",
        "comparison",
        "between",
        "versus",
        "vs",
        "difference",
        "differ",
    }

    @staticmethod
    def _semantic_root(word: str) -> str:
        """
        Produces a lightweight lexical root.

        This is intentionally conservative. It is not intended
        to be a complete stemming algorithm.

        Examples
        --------
        membership   -> member
        ownership    -> owner
        subscription -> subscription
        """

        if word.endswith("ship") and len(word) > 4:
            return word[:-4]

        return word

    @staticmethod
    def _common_prefix_length(
        first: str,
        second: str,
    ) -> int:
        """
        Returns the number of leading characters shared by
        two words.
        """

        length = 0

        for first_char, second_char in zip(
            first,
            second,
        ):
            if first_char != second_char:
                break

            length += 1

        return length

    @classmethod
    def _words_are_related(
        cls,
        column_word: str,
        question_word: str,
    ) -> bool:
        """
        Determines whether a schema word and question word
        provide strong lexical evidence for each other.

        Supports:

            membership  <-> members
            subscription <-> subscribers

        without hardcoding either relationship.
        """

        column_root = cls._semantic_root(
            column_word
        )

        question_root = cls._semantic_root(
            question_word
        )

        if (
            len(column_root) < 4
            or len(question_root) < 4
        ):
            return False

        # ------------------------------------
        # Direct prefix relationship
        #
        # member <-> members
        # ------------------------------------

        if (
            column_root.startswith(question_root)
            or question_root.startswith(column_root)
        ):
            return True

        # ------------------------------------
        # Strong common-prefix relationship
        #
        # subscription <-> subscriber
        # share "subscri..."
        #
        # Require a reasonably long prefix to
        # avoid weak accidental matches.
        # ------------------------------------

        common_prefix = cls._common_prefix_length(
            column_root,
            question_root,
        )

        shortest_length = min(
            len(column_root),
            len(question_root),
        )

        if (
            common_prefix >= 6
            and common_prefix / shortest_length >= 0.6
        ):
            return True

        return False

    @classmethod
    def parse(
        cls,
        text: str,
        schema,
        original_text: str | None = None,
    ) -> DimensionParseResult:

        normalized_text = normalize_text(text)

        comparison_source = normalize_text(
            original_text
            if original_text is not None
            else text
        )

        comparison_words = set(
            comparison_source.split()
        )

        # ----------------------------------------
        # Only activate for comparative language
        # ----------------------------------------

        if not (
            comparison_words
            & cls.COMPARISON_MARKERS
        ):
            return DimensionParseResult(
                cleaned_text=normalized_text,
                dimensions=[],
            )

        candidates = []

        question_words = set(
            normalized_text.split()
        )

        # ----------------------------------------
        # Score categorical / boolean columns
        # ----------------------------------------

        for column in schema:

            if column.is_numeric:
                continue

            score = 0

            # ------------------------------------
            # Exact column / alias evidence
            # ------------------------------------

            column_matches = ColumnMatcher.match(
                normalized_text,
                [column],
            )

            if column_matches:
                score += 3

            # ------------------------------------
            # Sample-value evidence
            # ------------------------------------

            for value in column.sample_values:

                if not isinstance(
                    value,
                    (str, bool),
                ):
                    continue

                value_text = normalize_text(
                    str(value)
                )

                if value_text in normalized_text:
                    score += 2

            # ------------------------------------
            # Boolean semantic evidence
            # ------------------------------------

            if column.is_boolean:

                column_words = set(
                    normalize_text(
                        column.normalized_name
                    ).split()
                )

                semantic_match = any(
                    cls._words_are_related(
                        column_word,
                        question_word,
                    )
                    for column_word in column_words
                    for question_word in question_words
                )

                if semantic_match:
                    score += 3

            if score > 0:
                candidates.append(
                    (score, column)
                )

        # ----------------------------------------
        # No defensible dimension
        # ----------------------------------------

        if not candidates:
            return DimensionParseResult(
                cleaned_text=normalized_text,
                dimensions=[],
            )

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_column = candidates[0]

        if best_score < 2:
            return DimensionParseResult(
                cleaned_text=normalized_text,
                dimensions=[],
            )

        # ----------------------------------------
        # Remove evidence belonging to resolved
        # comparison dimension
        # ----------------------------------------

        cleaned_words = normalized_text.split()

        column_words = set(
            normalize_text(
                best_column.normalized_name
            ).split()
        )

        filtered_words = []

        for word in cleaned_words:

            is_dimension_evidence = any(
                cls._words_are_related(
                    column_word,
                    word,
                )
                for column_word in column_words
            )

            if (
                is_dimension_evidence
                or word == "non"
            ):
                continue

            filtered_words.append(word)

        cleaned_text = " ".join(
            filtered_words
        )

        return DimensionParseResult(
            cleaned_text=cleaned_text,
            dimensions=[
                Dimension(
                    column=best_column.name
                )
            ],
        )