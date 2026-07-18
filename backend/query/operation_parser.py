from models.operation import Operation


class OperationParser:
    """
    Identifies the analytical operation requested by the user.

    Assumes the question has already been normalized by QueryNormalizer.
    """

    OPERATIONS = {
        # Statistical Operations (Canonical only)
        "average": Operation.MEAN,
        "sum": Operation.SUM,
        "count": Operation.COUNT,
        "maximum": Operation.MAX,
        "minimum": Operation.MIN,

        # Dataset Overview
        "describe": "describe",
        "summary": "describe",

        # Metadata
        "columns": "columns",
        "schema": "columns",
    }

    @classmethod
    def parse(cls, question: str) -> dict:

        normalized_question = question.lower()

        # -------------------------------
        # Dataset Preview
        # -------------------------------
        if "top" in normalized_question and "row" in normalized_question:

            remaining_text = normalized_question

            for word in ("top", "rows", "row"):
                remaining_text = remaining_text.replace(word, "", 1)

            remaining_text = " ".join(remaining_text.split())

            return {
                "operation": Operation.HEAD,
                "remaining_text": remaining_text,
            }

        if "bottom" in normalized_question and "row" in normalized_question:

            remaining_text = normalized_question

            for word in ("bottom", "rows", "row"):
                remaining_text = remaining_text.replace(word, "", 1)

            remaining_text = " ".join(remaining_text.split())

            return {
                "operation": Operation.TAIL,
                "remaining_text": remaining_text,
            }

        # -------------------------------
        # Statistical / Metadata Operations
        # -------------------------------
        words = normalized_question.split()

        for keyword, operation in cls.OPERATIONS.items():

            if keyword in words:

                words.remove(keyword)

                remaining_text = " ".join(words)

                return {
                    "operation": operation,
                    "remaining_text": remaining_text,
                }

        return {
            "operation": None,
            "remaining_text": normalized_question,
        }