import re

from data_models.base import BaseSlackModel


class Channel(BaseSlackModel):
    description: str | None = None

    main_workspace: str
    additional_workspaces: list[str]

    @property
    def db_collection(self) -> str:
        return "channels"

    @property
    def prepared_name(self):
        return re.sub(r"\s+", "-", self.name.lower())
