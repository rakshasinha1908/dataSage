from models.condition import Condition
from utils.text_utils import normalize_text


class FilterValueResolver:
    """
    Resolves remaining categorical and boolean values
    into filter conditions.

    Examples
    --------

    Categorical:

        "female patients"

            -> Gender == "Female"

    Boolean:

        "subscribers"

            -> Subscription Status == True

        "non members"

            -> Membership Customer == False

    Boolean resolution is schema-driven. It uses the
    semantic relationship between the user's words and
    the boolean column name / aliases rather than
    hardcoding dataset-specific column names.
    """

    NEGATION_WORDS = {
        "non",
        "not",
        "without",
    }

    # =========================================================
    # Generic word helpers
    # =========================================================

    @staticmethod
    def _singularize(word: str) -> str:
        """
        Lightweight normalization for common plural forms.

        This is intentionally conservative. It is not intended
        to be a full linguistic stemmer.
        """

        if word.endswith("ies") and len(word) > 3:
            return word[:-3] + "y"

        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]

        return word

    @classmethod
    def _semantic_root(cls, word: str) -> str:
        word = cls._singularize(word)

        if word.endswith("ship") and len(word) > 4:
            word = word[:-4]

        return word
    
    # =========================================================
    # Boolean resolution
    # =========================================================

    @classmethod
    def _resolve_boolean_filters(
        cls,
        normalized_text: str,
        schema,
    ):
        """
        Resolve semantic references to boolean columns.

        Example:

            schema:
                Subscription Status -> bool

            text:
                "subscribers"

            result:
                Subscription Status == True
        """

        conditions = []
        remaining_words = normalized_text.split()

        for column in schema:

            if not column.is_boolean:
                continue

            # -----------------------------------------
            # Build semantic vocabulary for the column
            # from its normalized name and aliases.
            # -----------------------------------------

            candidate_phrases = {
                normalize_text(column.normalized_name),
            }

            for alias in column.aliases:
                candidate_phrases.add(
                    normalize_text(alias)
                )

            column_roots = set()

            for phrase in candidate_phrases:

                for word in phrase.split():

                    root = cls._semantic_root(word)

                    if len(root) >= 4:
                        column_roots.add(root)

            if not column_roots:
                continue

            # -----------------------------------------
            # Find user words semantically related to
            # this boolean column.
            # -----------------------------------------

            matched_indexes = []

            for index, word in enumerate(remaining_words):

                if word in cls.NEGATION_WORDS:
                    continue

                word_root = cls._semantic_root(word)

                if len(word_root) < 4:
                    continue

                if any(
                    word_root.startswith(column_root)
                    or column_root.startswith(word_root)
                    for column_root in column_roots
                ):
                    matched_indexes.append(index)

            if not matched_indexes:
                continue

            # -----------------------------------------
            # Determine boolean value.
            #
            # "subscriber"       -> True
            # "non subscriber"   -> False
            # "not subscriber"   -> False
            # "without membership" -> False
            # -----------------------------------------

            is_negative = False
            consumed_indexes = set(matched_indexes)

            for index in matched_indexes:

                previous_index = index - 1

                if (
                    previous_index >= 0
                    and remaining_words[previous_index]
                    in cls.NEGATION_WORDS
                ):
                    is_negative = True
                    consumed_indexes.add(
                        previous_index
                    )

            value = not is_negative

            conditions.append(
                Condition(
                    column=column.name,
                    operator="==",
                    value=value,
                )
            )

            # -----------------------------------------
            # Remove only the words that supplied
            # evidence for this condition.
            # -----------------------------------------

            remaining_words = [
                word
                for index, word in enumerate(remaining_words)
                if index not in consumed_indexes
            ]

        cleaned_text = " ".join(
            remaining_words
        )

        return conditions, cleaned_text

    # =========================================================
    # Categorical resolution
    # =========================================================

    @classmethod
    def _resolve_categorical_filters(
        cls,
        normalized_text: str,
        schema,
    ):
        """
        Resolve literal categorical sample values.

        Example:

            "female patients"

                -> Gender == "Female"
        """

        conditions = []

        for column in schema:

            for sample_value in column.sample_values:

                if not isinstance(sample_value, str):
                    continue

                normalized_value = normalize_text(
                    sample_value
                )

                if (
                    normalized_value
                    not in normalized_text
                ):
                    continue

                conditions.append(
                    Condition(
                        column=column.name,
                        operator="==",
                        value=sample_value,
                    )
                )

                normalized_text = (
                    normalized_text.replace(
                        normalized_value,
                        "",
                        1,
                    )
                )

        cleaned_text = " ".join(
            normalized_text.split()
        )

        return conditions, cleaned_text

    # =========================================================
    # Public resolver
    # =========================================================

    @classmethod
    def resolve(
        cls,
        text: str,
        schema,
    ):
        normalized_text = normalize_text(text)

        conditions = []

        # -----------------------------------------
        # 1. Literal categorical values
        # -----------------------------------------

        (
            categorical_conditions,
            remaining_text,
        ) = cls._resolve_categorical_filters(
            normalized_text,
            schema,
        )

        conditions.extend(
            categorical_conditions
        )

        # -----------------------------------------
        # 2. Semantic boolean values
        # -----------------------------------------

        (
            boolean_conditions,
            remaining_text,
        ) = cls._resolve_boolean_filters(
            remaining_text,
            schema,
        )

        conditions.extend(
            boolean_conditions
        )

        cleaned_text = " ".join(
            remaining_text.split()
        )

        return conditions, cleaned_text