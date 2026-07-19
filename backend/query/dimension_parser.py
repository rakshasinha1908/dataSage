from models.dimension import Dimension
from models.dimension_parse_result import DimensionParseResult
from query.column_matcher import ColumnMatcher
from utils.text_utils import (
    normalize_text,
    remove_connector_words,
)


class DimensionParser:
    """
    Extracts grouping dimensions from the user's question.
    """

    @classmethod
    def parse(
        cls,
        text: str,
        schema,
    ):

        normalized_text = normalize_text(text)
        cleaned_text = normalized_text

        dimensions = []

        grouping_keywords = {
            "by",
            "per",
        }

        words = normalized_text.split()

        for index, word in enumerate(words):

            if word not in grouping_keywords:
                continue

            if index + 1 >= len(words):
                continue

            candidate = words[index + 1]

            matched_columns = ColumnMatcher.match(
                candidate,
                schema,
            )

            if not matched_columns:
                continue

            column = matched_columns[0]

            dimensions.append(
                Dimension(
                    column=column.name,
                )
            )

            cleaned_text = cleaned_text.replace(
                f"{word} {candidate}",
                "",
            )

        cleaned_text = " ".join(cleaned_text.split())
        cleaned_text = remove_connector_words(cleaned_text)

        return DimensionParseResult(
            cleaned_text=cleaned_text,
            dimensions=dimensions,
        )