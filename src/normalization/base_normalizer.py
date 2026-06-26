from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class BaseNormalizer(ABC):
    """
    Base class for all data normalizers.
    """

    def __init__(self, input_file: Path, output_file: Path):
        self.input_file = input_file
        self.output_file = output_file

        self.raw_df: pd.DataFrame | None = None
        self.normalized_df: pd.DataFrame | None = None

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def normalize(self):
        pass

    @abstractmethod
    def save(self):
        pass