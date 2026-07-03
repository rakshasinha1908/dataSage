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
    def parse(cls, question: str) -> str | None:

        question = question.lower()

        for keyword, operation in cls.OPERATIONS.items():

            if keyword in question:
                return operation

        return None