class DatasetDescriptionRequestBuilder:

    @staticmethod
    def build(
        dataset,
        question: str,
    ) -> str:

        overview = DatasetDescriptionRequestBuilder._build_dataset_overview(
            dataset,
        )

        schema = DatasetDescriptionRequestBuilder._build_schema_context(
            dataset,
        )

        instructions = DatasetDescriptionRequestBuilder._build_instructions()

        return f"""
{overview}

{schema}

User Question
-------------
{question}

{instructions}
"""

    @staticmethod
    def _build_dataset_overview(dataset) -> str:
        """
        Builds a high-level summary of the uploaded dataset.
        """
        return f"""
Dataset Overview
================

Filename: {dataset.filename}

Rows: {len(dataset.dataframe)}

Columns: {len(dataset.schema)}
"""

    @staticmethod
    def _get_display_type(column) -> str:
        """
        Converts internal pandas dtypes into user-friendly types.
        """
        if column.is_numeric:
            return "Numeric"

        if column.is_boolean:
            return "Boolean"

        if column.is_datetime:
            return "Date"

        return "Categorical / Text"
    
    @staticmethod
    def _build_schema_context(dataset) -> str:
        """
        Builds a readable schema description for the LLM.
        """
        schema_lines = [
            "Schema",
            "======",
            "",
        ]

        for column in dataset.schema:
            schema_lines.extend(
                [
                    f"Column: {column.name}",
                    f"Type: {DatasetDescriptionRequestBuilder._get_display_type(column)}",
                    f"Unique Values: {column.unique_count}",
                    f"Nullable: {'Yes' if column.nullable else 'No'}",
                ]
            )

            if column.sample_values:
                samples = ", ".join(map(str, column.sample_values))
                schema_lines.append(
                    f"Sample Values: {samples}"
                )

            schema_lines.append("")

        return "\n".join(schema_lines)

    @staticmethod
    def _build_instructions() -> str:
        """
        Instructions for generating an executive summary
        of the uploaded dataset.
        """
        return """
Instructions
============

You are DataSage, an experienced AI data analyst.

A user has just uploaded a dataset and wants to quickly understand it before asking analytical questions.

Your goal is NOT to document the schema.
Your goal is to write a concise executive summary that helps the user understand the dataset.

Structure your response using exactly these sections:

## 📝 Summary
Write 1–2 short paragraphs explaining:
- what the dataset appears to represent
- what each row likely corresponds to
- the overall purpose of the dataset

Infer the purpose naturally from the schema and sample values.

## 📦 What's Included
Summarize the information captured by grouping related columns together.

For example:
- Customer information
- Product details
- Transaction information
- Medical information
- Location details

Do NOT list every column one by one.

## 💡 Questions You Can Explore
Suggest 4–6 meaningful analytical questions that can be answered using this dataset.

Examples:
- Which products generate the highest revenue?
- Does age affect hospital stay?
- Which cities have the highest average sales?

These should inspire the user to explore the dataset.

Rules
-----

Do NOT invent:
- statistics
- trends
- correlations
- conclusions that require computation

You MAY infer:
- the domain of the dataset
- what each record represents
- what kinds of analyses are possible

Write naturally, like an experienced data analyst explaining a newly received dataset to a colleague.

Use Markdown.

Keep the response concise, informative, and engaging.
"""
