from utils.text_utils import normalize_text


class ColumnAliasGenerator:
    """
    Generates generic aliases for dataset columns.

    Examples
    --------
    product_category
        -> product category
        -> category
        -> categories

    customer_full_name
        -> customer full name
        -> customer name
        -> name
        -> names

    city
        -> city
        -> cities
    """

    @classmethod
    def generate(
        cls,
        normalized_name: str,
    ) -> list[str]:

        normalized_name = normalize_text(normalized_name)

        aliases = set()

        words = normalized_name.split()

        # Always include the normalized name itself
        aliases.add(normalized_name)

        # ----------------------------
        # Last word
        # ----------------------------

        if words:
            last = words[-1]

            aliases.add(last)

            plural = cls._pluralize(last)
            aliases.add(plural)

        # ----------------------------
        # Drop common prefixes
        # ----------------------------

        prefixes = {
            "customer",
            "product",
            "transaction",
            "order",
            "membership",
            "discount",
            "phone",
        }

        filtered = [
            word
            for word in words
            if word not in prefixes
        ]

        if filtered:

            phrase = " ".join(filtered)

            aliases.add(phrase)
            aliases.add(cls._pluralize(phrase))

        return sorted(alias for alias in aliases if alias)

    @staticmethod
    def _pluralize(word: str) -> str:

        if word.endswith("y"):
            return word[:-1] + "ies"

        if word.endswith("s"):
            return word

        return word + "s"