from models.dimension import Dimension
from models.dimension_parse_result import DimensionParseResult
from query.column_matcher import ColumnMatcher
from utils.text_utils import (
    normalize_text,
    remove_connector_words,
    remove_filler_words,
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

            matched_column = None
            matched_phrase = None

            phrase_words = words[index + 1:]

            for start in range(0, len(phrase_words)):
                for end in range(len(phrase_words), start, -1):

                    candidate = " ".join(phrase_words[start:end])

                    matched_columns = ColumnMatcher.match(
                        candidate,
                        schema,
                    )

                    if matched_columns:
                        matched_column = matched_columns[0]
                        matched_phrase = candidate
                        break

                if matched_column:
                    break

            if not matched_column:
                continue

            dimensions.append(
                Dimension(
                    column=matched_column.name,
                )
            )

            cleaned_text = cleaned_text.replace(
                f"{word} {matched_phrase}",
                "",
                1,
            )

        cleaned_text = " ".join(cleaned_text.split())
        cleaned_text = remove_connector_words(cleaned_text)
        
        cleaned_text = " ".join(cleaned_text.split())
        cleaned_text = remove_filler_words(cleaned_text)
        cleaned_text = remove_connector_words(cleaned_text)

        return DimensionParseResult(
            cleaned_text=cleaned_text,
            dimensions=dimensions,
        )
