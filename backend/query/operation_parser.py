from models.operation import Operation
class OperationParser:
    """
    Identifies the analytical operation requested by the user.
    """

    OPERATIONS = {
        # Statistical Operations
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



        if (
            ("top" in normalized_question or "first" in normalized_question)
            and "row" in normalized_question
        ):
            return {
                "operation": Operation.HEAD,
                "remaining_text": "",
            }

        if (
            ("bottom" in normalized_question or "last" in normalized_question)
            and "row" in normalized_question
        ):
            return {
                "operation": Operation.TAIL,
                "remaining_text": "",
            }

    

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