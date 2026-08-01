from utils.text_utils import normalize_text


class ColumnAliasGenerator:
    """
    Generates structural aliases directly from a column name.

    The generator is intentionally dataset-agnostic.

    It does not contain domain-specific words such as
    "customer", "product", "transaction", etc.

    Examples
    --------
    customer_full_name
        -> customer full name
        -> full name
        -> name
        -> names

    product_category
        -> product category
        -> category
        -> categories

    favorite_cartoon
        -> favorite cartoon
        -> cartoon
        -> cartoons

    subscription_status
        -> subscription status
        -> status
        -> statuses
    """

    @classmethod
    def generate(
        cls,
        normalized_name: str,
    ) -> list[str]:

        normalized_name = normalize_text(
            normalized_name
        )

        words = normalized_name.split()

        if not words:
            return []

        aliases = {
            normalized_name,
        }

        # ----------------------------------------
        # Generate progressively shorter suffixes
        #
        # customer full name
        #     -> full name
        #     -> name
        #
        # product category
        #     -> category
        #
        # viewing time hours
        #     -> time hours
        #     -> hours
        # ----------------------------------------

        for start_index in range(1, len(words)):

            phrase = " ".join(
                words[start_index:]
            )

            if phrase:
                aliases.add(phrase)

        # ----------------------------------------
        # Add plural form of the final concept
        # ----------------------------------------

        last_word = words[-1]

        aliases.add(last_word)
        aliases.add(
            cls._pluralize(last_word)
        )

        return sorted(
            alias
            for alias in aliases
            if alias
        )

    @staticmethod
    def _pluralize(word: str) -> str:

        if word.endswith(
            ("s", "x", "z", "ch", "sh")
        ):
            return word + "es"

        if (
            word.endswith("y")
            and len(word) > 1
            and word[-2] not in "aeiou"
        ):
            return word[:-1] + "ies"

        return word + "s"