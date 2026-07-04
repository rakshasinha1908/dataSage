class OperationParser:
    """
    Identifies the analytical operation requested by the user.
    """

    OPERATIONS = {
        "average": "mean",
        "avg": "mean",
        "mean": "mean",

        "sum": "sum",
        "total": "sum",

        "count": "count",
        "number": "count",

        "maximum": "max",
        "max": "max",
        "highest": "max",

        "minimum": "min",
        "min": "min",
        "lowest": "min",
    }

    @classmethod
    def parse(cls, question: str) -> dict:
        normalized_question = question.lower()

        for keyword, operation in cls.OPERATIONS.items():
            if keyword in normalized_question:
                remaining_text = normalized_question.replace(keyword, "", 1)
                remaining_text = " ".join(remaining_text.split())

                return {
                    "operation": operation,
                    "remaining_text": remaining_text,
                }

        return {
            "operation": None,
            "remaining_text": normalized_question,
        }
