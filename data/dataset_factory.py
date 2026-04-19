import pathlib
from enum import IntEnum
from data.csv.csv_utils import get_csv_content, preprocess_csv_data


class DatasetSources(IntEnum):
    CSV = 1


class DatasetFactory:
    _DEFAULT_CSV = "csv/fc26_players.csv"

    @classmethod
    def create(cls, source: DatasetSources = DatasetSources.CSV, csv_path: str | None = None):
        if source == DatasetSources.CSV:
            return cls._get_dataset_from_csv(csv_path)
        raise ValueError(f"Fonte de dados não suportada: {source}")

    @classmethod
    def _get_dataset_from_csv(cls, csv_path: str | None = None):
        filename = csv_path or cls._DEFAULT_CSV
        filepath = pathlib.Path(__file__).parent.joinpath(filename)
        dataset = get_csv_content(filepath)
        preprocess_csv_data(dataset)
        return dataset
