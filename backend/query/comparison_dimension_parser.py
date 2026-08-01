from models.dimension import Dimension
from models.dimension_parse_result import DimensionParseResult
from query.column_matcher import ColumnMatcher
from utils.text_utils import normalize_text


class ComparisonDimensionParser:
    """
    Resolves implicit grouping dimensions from
    comparative language.

    Comparison intent is detected from the original
    question, while dimension evidence is resolved
    from the remaining analytical text.

    Examples
    --------
    compare between members and non members
    compare male and female patients
    difference between prepaid and non prepaid orders

    Resolution is based on categorical / boolean
    sample values and column semantics rather than
    dataset-specific column names.
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
        # based on evidence in remaining text.
        # ----------------------------------------

        for column in schema:

            if column.is_numeric:
                continue

            score = 0

            # ------------------------------------
            # Column-name / alias evidence
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

                for column_word in column_words:

                    # Generic lightweight stemming.
                    #
                    # membership -> member
                    # ownership  -> owner
                    #
                    # Other words remain unchanged.
                    if column_word.endswith("ship"):
                        root = column_word[:-4]
                    else:
                        root = column_word

                    if len(root) < 4:
                        continue

                    if any(
                        word.startswith(root)
                        or root.startswith(word)
                        for word in question_words
                        if len(word) >= 4
                    ):
                        score += 3
                        break

            if score > 0:
                candidates.append(
                    (score, column)
                )

        # ----------------------------------------
        # No defensible dimension found
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
        # Remove evidence belonging to the
        # resolved comparison dimension.
        # ----------------------------------------

        cleaned_words = normalized_text.split()

        column_words = set(
            normalize_text(
                best_column.normalized_name
            ).split()
        )

        semantic_roots = set()

        for column_word in column_words:

            if column_word.endswith("ship"):
                root = column_word[:-4]
            else:
                root = column_word

            if len(root) >= 4:
                semantic_roots.add(root)

        filtered_words = []

        for word in cleaned_words:

            is_dimension_evidence = any(
                word.startswith(root)
                or root.startswith(word)
                for root in semantic_roots
                if len(word) >= 4
            )

            # "non" belongs to expressions such as
            # "non members" once that comparison
            # dimension has been resolved.
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