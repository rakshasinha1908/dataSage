from models.column_schema import ColumnSchema
from models.dataset import Dataset


class SchemaEngine:
    """
    Generates schema information for a dataset.
    """

    @staticmethod
    def generate(dataset: Dataset) -> Dataset:

        schema = []

        dataframe = dataset.dataframe

        for column in dataframe.columns:

            series = dataframe[column]

            column_schema = ColumnSchema(
                name=column,
                dtype=str(series.dtype),
                nullable=series.isnull().any(),
                unique_count=series.nunique(dropna=True),
                sample_values=series.dropna().unique().tolist()[:5]
            )

            schema.append(column_schema)

        dataset.schema = schema

        return dataset