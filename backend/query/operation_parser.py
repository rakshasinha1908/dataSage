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
        "describe": Operation.DESCRIBE,
        "summary": Operation.DESCRIBE,

        # Metadata
        "columns": Operation.COLUMNS,
        "schema": Operation.COLUMNS,
    }

    @classmethod
    def parse(cls, question: str) -> dict:
        
        print("\n" + "=" * 60)
        print("🔥 OPERATION PARSER IS RUNNING")
        print("INPUT:", repr(question))
        print("=" * 60)

        normalized_question = question.lower().strip()

        # ----------------------------------------
        # Dataset Preview (Top / Bottom)
        # ----------------------------------------

        if "top" in normalized_question and (
            "row" in normalized_question
            or "rows" in normalized_question
            or "record" in normalized_question
            or "records" in normalized_question
        ):

            remaining_text = normalized_question

            for word in (
                "top",
                "rows",
                "row",
                "records",
                "record",
            ):
                remaining_text = remaining_text.replace(word, "", 1)

            remaining_text = " ".join(remaining_text.split())

            return {
                "operation": Operation.HEAD,
                "remaining_text": remaining_text,
            }

        if "bottom" in normalized_question and (
            "row" in normalized_question
            or "rows" in normalized_question
            or "record" in normalized_question
            or "records" in normalized_question
        ):

            remaining_text = normalized_question

            for word in (
                "bottom",
                "rows",
                "row",
                "records",
                "record",
            ):
                remaining_text = remaining_text.replace(word, "", 1)

            remaining_text = " ".join(remaining_text.split())

            return {
                "operation": Operation.TAIL,
                "remaining_text": remaining_text,
            }

        # ----------------------------------------
        # Row Retrieval
        # ----------------------------------------

        words = normalized_question.split()

        retrieval_verbs = {
            "show",
            "display",
            "list",
        }

        row_words = {
            "row",
            "rows",
            "record",
            "records",
            "data",
        }

        if (
            any(word in retrieval_verbs for word in words)
            and any(word in row_words for word in words)
        ):

            remaining_text = normalized_question

            # Remove verb
            for phrase in (
                "show me",
                "show",
                "display",
                "list",
            ):
                remaining_text = remaining_text.replace(
                    phrase,
                    "",
                    1,
                )

            remaining_text = " ".join(remaining_text.split())

            return {
                "operation": Operation.SHOW_ROWS,
                "remaining_text": remaining_text,
            }

        # ----------------------------------------
        # Statistical / Metadata Operations
        # ----------------------------------------

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