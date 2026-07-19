from models.column_schema import ColumnSchema
from models.dataset import Dataset
from utils.text_utils import normalize_text

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
                name=str(column),
                normalized_name=normalize_text(str(column)),
                dtype=str(series.dtype),
                nullable=bool(series.isnull().any()),
                unique_count=int(series.nunique(dropna=True)),
                sample_values=[
                    value.item() if hasattr(value, "item") else value
                    for value in series.dropna().unique().tolist()[:5]
                ]
            )
            
            print(
                column_schema.name,
                column_schema.dtype,
                column_schema.sample_values,
            )

            schema.append(column_schema)

        dataset.schema = schema

        return dataset