import csv
from contextlib import contextmanager
from typing import ContextManager

from data_models.instruction_entry import InstructionEntry


class CSVInstructionManager:
    def __init__(self, filename: str):
        self.filename = filename

        self._current_file = None
        self._csv_dict_writer = None

    @contextmanager
    def open_for_writing(
        self,
    ) -> ContextManager:
        with open(self.filename, "w") as file:
            self._current_file = file
            self._csv_dict_writer = csv.DictWriter(
                file, fieldnames=InstructionEntry.model_fields.keys()
            )
            self._csv_dict_writer.writeheader()
            yield file
        self._current_file = None
        self._csv_dict_writer = None

    def add_entry(self, entry: InstructionEntry):
        if not isinstance(entry, InstructionEntry):
            raise ValueError(f"Expected InstructionEntry, got {type(entry)}")
        if not self._current_file:
            raise ValueError("No file opened")

        self._csv_dict_writer.writerow(entry.model_dump())

    def read_entries(self):
        with open(self.filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield InstructionEntry(**row)
