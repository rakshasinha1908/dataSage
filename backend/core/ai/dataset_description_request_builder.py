class DatasetDescriptionRequestBuilder:
    """
    Builds prompts for conversational questions about
    the uploaded dataset.

    The dataset context is factual grounding for the AI.
    The user's actual question determines the response.
    """

    @staticmethod
    def build(
        dataset,
        question: str,
    ) -> str:

        overview = (
            DatasetDescriptionRequestBuilder
            ._build_dataset_overview(dataset)
        )

        schema = (
            DatasetDescriptionRequestBuilder
            ._build_schema_context(dataset)
        )

        instructions = (
            DatasetDescriptionRequestBuilder
            ._build_instructions()
        )

        return f"""
You are DataSage, an experienced AI data analyst.

The user has uploaded a dataset and is asking a question
about the dataset itself.

Use the dataset context below to answer the user's
specific question.

{overview}

{schema}

User Question
=============
{question}

{instructions}
"""

    @staticmethod
    def _build_dataset_overview(dataset) -> str:
        """
        Builds high-level factual dataset context.
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
        Converts internal column metadata into
        user-friendly types.
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
        Builds factual schema context for the AI.
        """

        schema_lines = [
            "Dataset Schema",
            "==============",
            "",
        ]

        for column in dataset.schema:

            schema_lines.extend(
                [
                    f"Column: {column.name}",
                    (
                        "Type: "
                        f"{DatasetDescriptionRequestBuilder._get_display_type(column)}"
                    ),
                    f"Unique Values: {column.unique_count}",
                    (
                        "Nullable: "
                        f"{'Yes' if column.nullable else 'No'}"
                    ),
                ]
            )

            if column.sample_values:

                samples = ", ".join(
                    map(str, column.sample_values)
                )

                schema_lines.append(
                    f"Sample Values: {samples}"
                )

            schema_lines.append("")

        return "\n".join(schema_lines)

    @staticmethod
    def _build_instructions() -> str:
        """
        General instructions for conversational
        dataset-understanding responses.
        """

        return """
Instructions
============

Answer the user's specific question directly.

Use the dataset overview, schema, column metadata,
and sample values as your factual context.

Adapt the response to what the user actually asked.

Examples:

- If the user asks to describe or summarize the dataset,
  provide a concise executive overview of what the
  dataset represents, what each row likely represents,
  and the main categories of information available.

- If the user asks what information the dataset contains,
  explain the main types of information captured.
  Group related fields naturally instead of listing
  every column mechanically.

- If the user asks what questions they can ask,
  focus primarily on useful analytical questions that
  can be answered using the available columns.

- If the user asks what they can analyze or explore,
  explain the major analytical directions available
  and give useful examples.

- If the user asks about a particular column or concept,
  answer only that question using the available dataset
  context.

Do not force every response into the same template.

Do not automatically provide a full dataset summary
unless the user actually asks for one.

Do not invent:
- statistics
- trends
- correlations
- rankings
- distributions
- causal relationships
- analytical conclusions that require computation

You may infer:
- the likely domain of the dataset
- what a row likely represents
- how related columns can be grouped
- what kinds of analyses the available fields support

Clearly distinguish reasonable structural inference
from verified analytical findings.

Do not perform calculations yourself.

If answering the question would require actual analysis
of the dataset rather than understanding its structure,
tell the user what analytical question they can ask
DataSage instead.

Use Markdown when it improves readability.

Keep the response concise, useful, and conversational.
"""