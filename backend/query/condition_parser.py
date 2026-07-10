from models.condition import Condition
from utils.text_utils import (normalize_text, remove_connector_words)
from models.condition_parse_result import ConditionParseResult

class ConditionParser:
    """
    Extracts filtering conditions from the user's question.
    """

    @classmethod
    def parse(cls, text: str, schema):

        normalized_question = normalize_text(text)
        cleaned_text = normalized_question

        conditions = []

        for column in schema:
            for value in column.sample_values:

                # Skip non-text values for now
                if not isinstance(value, str):
                    continue

                normalized_value = normalize_text(value)

                if normalized_value in cleaned_text:
                    conditions.append(
                        Condition(
                            column=column.name,
                            operator="==",
                            value=value,
                        )
                    )

                    cleaned_text = cleaned_text.replace(
                        normalized_value,
                        ""
                    )
                    
        cleaned_text = " ".join(cleaned_text.split())
        cleaned_text = remove_connector_words(cleaned_text)
        
        return ConditionParseResult(
            cleaned_text=cleaned_text,
            conditions=conditions,
        )
