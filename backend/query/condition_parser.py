from models.condition import Condition
from models.condition_parse_result import ConditionParseResult
from utils.text_utils import normalize_text, remove_connector_words

import re


class ConditionParser:
    """
    Extracts filtering conditions from the user's question.

    Supported patterns:
        where <column> is <value>
        <column> is <value>
        <column> = <value>
        <column> equals <value>

    Also supports boolean columns:

        membership customer is yes
        prepaid order is no
        discount applied = true

    Returns:
        - extracted conditions
        - remaining text for downstream parsers
    """

    BOOLEAN_ALIASES = {
        True: ["true", "yes", "y", "1"],
        False: ["false", "no", "n", "0"],
    }

    @classmethod
    def parse(cls, text: str, schema):

        normalized_question = normalize_text(text)
        cleaned_text = normalized_question

        conditions = []

        # -------------------------------------------------
        # Longest values first.
        # Prevents:
        #   "red" matching before "dark red"
        # -------------------------------------------------
        candidates = []

        for column in schema:
            for value in column.sample_values:

                # -----------------------------------------
                # Boolean values
                # -----------------------------------------
                if isinstance(value, bool):

                    for alias in cls.BOOLEAN_ALIASES[value]:
                        candidates.append(
                            (
                                len(alias),
                                column,
                                value,
                                alias,
                            )
                        )
                    continue

                # -----------------------------------------
                # String values
                # -----------------------------------------
                if isinstance(value, str):
                    normalized_value = normalize_text(value)

                    candidates.append(
                        (
                            len(normalized_value),
                            column,
                            value,
                            normalized_value,
                        )
                    )

        candidates.sort(reverse=True, key=lambda x: x[0])

        # -------------------------------------------------
        # Extract conditions
        # -------------------------------------------------
        for _, column, original_value, normalized_value in candidates:

            column_name = normalize_text(column.name)

            patterns = [
                rf"\bwhere\s+{re.escape(column_name)}\s+is\s+{re.escape(normalized_value)}\b",
                rf"\b{re.escape(column_name)}\s+is\s+{re.escape(normalized_value)}\b",
                rf"\b{re.escape(column_name)}\s*=\s*{re.escape(normalized_value)}\b",
                rf"\b{re.escape(column_name)}\s+equals\s+{re.escape(normalized_value)}\b",
            ]

            for pattern in patterns:

                if re.search(pattern, cleaned_text):
                    conditions.append(
                        Condition(
                            column=column.name,
                            operator="==",
                            value=original_value,
                        )
                    )

                    cleaned_text = re.sub(
                        pattern,
                        " ",
                        cleaned_text,
                        count=1,
                    )

                    break

        # -------------------------------------------------
        # Cleanup
        # -------------------------------------------------
        cleaned_text = " ".join(cleaned_text.split())
        cleaned_text = remove_connector_words(cleaned_text)
        cleaned_text = " ".join(cleaned_text.split())

        return ConditionParseResult(
            cleaned_text=cleaned_text,
            conditions=conditions,
        )