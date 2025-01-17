import csv
from contextlib import contextmanager
from typing import ContextManager, Type, Generator, Union

from data_models.instruction_entries import (
    AddUserInstructionEntry,
    AssignAdminOwnerInstructionEntry,
)


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
                file, fieldnames=AddUserInstructionEntry.model_fields.keys()
            )
            self._csv_dict_writer.writeheader()
            yield file
        self._current_file = None
        self._csv_dict_writer = None

    def add_entry(self, entry: AddUserInstructionEntry):
        if not isinstance(entry, AddUserInstructionEntry):
            raise ValueError(f"Expected InstructionEntry, got {type(entry)}")
        if not self._current_file:
            raise ValueError("No file opened")

        self._csv_dict_writer.writerow(entry.model_dump())

    def read_entries(
        self,
        instructions_type: (
            Type[AddUserInstructionEntry] | Type[AssignAdminOwnerInstructionEntry]
        ),
    ) -> Generator[
        Union[AddUserInstructionEntry, AssignAdminOwnerInstructionEntry], None, None
    ]:
        """
        Reads instruction entries from a CSV file

        :param instructions_type: The type of InstructionEntry to create
        :return: A generator of InstructionEntry objects
        """
        with open(self.filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield instructions_type(**row)
