from data_models.base import BaseSlackModel


class Workspace(BaseSlackModel):
    @property
    def of_type(self) -> str:
        return "workspace"
