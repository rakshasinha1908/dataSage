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

    RETRIEVAL_VERBS = {
        "show",
        "display",
        "list",
    }

    ROW_WORDS = {
        "row",
        "rows",
        "record",
        "records",
        "data",
    }

    @classmethod
    def parse(cls, question: str) -> dict:

        normalized_question = question.lower().strip()
        words = normalized_question.split()

        # ----------------------------------------
        # Dataset Preview (Top)
        # ----------------------------------------

        if (
            "top" in words
            and any(
                word in cls.ROW_WORDS
                for word in words
            )
        ):
            remaining_text = normalized_question

            # Keep "top" so RankingParser can
            # detect direction / limit.
            for word in (
                "rows",
                "row",
                "records",
                "record",
            ):
                remaining_text = remaining_text.replace(
                    word,
                    "",
                    1,
                )

            remaining_text = " ".join(
                remaining_text.split()
            )

            return {
                "operation": Operation.HEAD,
                "remaining_text": remaining_text,
            }

        # ----------------------------------------
        # Dataset Preview (Bottom)
        # ----------------------------------------

        if (
            "bottom" in words
            and any(
                word in cls.ROW_WORDS
                for word in words
            )
        ):
            remaining_text = normalized_question

            # Keep "bottom" so RankingParser can
            # detect direction / limit.
            for word in (
                "rows",
                "row",
                "records",
                "record",
            ):
                remaining_text = remaining_text.replace(
                    word,
                    "",
                    1,
                )

            remaining_text = " ".join(
                remaining_text.split()
            )

            return {
                "operation": Operation.TAIL,
                "remaining_text": remaining_text,
            }

        # ----------------------------------------
        # Statistical / Metadata Operations
        #
        # These must be checked BEFORE generic
        # row retrieval.
        #
        # Example:
        #   "show average sales by city"
        #
        # must remain MEAN, not SHOW_ROWS.
        # ----------------------------------------

        for keyword, operation in cls.OPERATIONS.items():

            if keyword in words:

                remaining_words = words.copy()
                remaining_words.remove(keyword)

                # Remove harmless presentation verbs.
                #
                # Example:
                #   "show average sales"
                #       -> average operation
                #       -> remaining: "sales"
                remaining_words = [
                    word
                    for word in remaining_words
                    if word not in cls.RETRIEVAL_VERBS
                ]

                remaining_text = " ".join(
                    remaining_words
                )

                return {
                    "operation": operation,
                    "remaining_text": remaining_text,
                }

        # ----------------------------------------
        # Row Retrieval
        #
        # If the user explicitly starts with a
        # retrieval verb and no analytical operation
        # was found above, interpret the request as
        # asking for matching rows.
        #
        # This allows:
        #
        #   show viewers with age > 15
        #   show patients with age > 50
        #   list customers in Delhi
        #   display orders above 1000
        #
        # without knowing what entity the dataset
        # represents.
        # ----------------------------------------

        if (
            words
            and words[0] in cls.RETRIEVAL_VERBS
        ):
            remaining_words = words[1:]

            # Handle "show me ..."
            if (
                remaining_words
                and remaining_words[0] == "me"
            ):
                remaining_words = remaining_words[1:]

            remaining_text = " ".join(
                remaining_words
            )

            return {
                "operation": Operation.SHOW_ROWS,
                "remaining_text": remaining_text,
            }

        # ----------------------------------------
        # No explicit operation
        # ----------------------------------------

        return {
            "operation": None,
            "remaining_text": normalized_question,
        }