import re

from data_models.base import BaseSlackModel


class Channel(BaseSlackModel):
    description: str | None = None

    main_workspace: str
    additional_workspaces: list[str]

    @property
    def of_type(self) -> str:
        return "channel"

    @property
    def prepared_name(self):
        return re.sub(r"\s+", "-", self.name.lower())
