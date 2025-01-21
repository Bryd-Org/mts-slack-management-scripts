import csv
from contextlib import contextmanager
from typing import ContextManager, Generator

from data_models.instruction_entries import (
    AddUserInstructionEntry,
    AssignAdminOwnerInstructionEntry,
    DeactivateRemoveUserInstructionEntry,
    InviteNewUserInstructionEntry,
)


class CSVInstructionManager:
    def __init__(self, filename: str):
        self.filename = filename

        self._current_file = None
        self._csv_dict_writer = None

        with open(self.filename, "r") as file:
            self.total_instructions = sum(1 for _ in file)
            self.total_instructions -= 1

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

    def _read_entries(
        self,
        instructions_type,
    ) -> Generator:
        """
        Reads instruction entries from a CSV file

        :param instructions_type: The type of InstructionEntry to create
        :return: A generator of InstructionEntry objects
        """
        with open(self.filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield instructions_type(**row)

    def yield_add_user_instructions(
        self,
    ) -> Generator[AddUserInstructionEntry, None, None]:
        yield from self._read_entries(AddUserInstructionEntry)

    def yield_assign_admin_owner_instructions(
        self,
    ) -> Generator[AssignAdminOwnerInstructionEntry, None, None]:
        yield from self._read_entries(AssignAdminOwnerInstructionEntry)

    def yield_deactivate_remove_user_instructions(
        self,
    ) -> Generator[DeactivateRemoveUserInstructionEntry, None, None]:
        yield from self._read_entries(DeactivateRemoveUserInstructionEntry)

    def yield_invite_new_users_instructions(
        self,
    ) -> Generator[InviteNewUserInstructionEntry, None, None]:
        yield from self._read_entries(InviteNewUserInstructionEntry)
