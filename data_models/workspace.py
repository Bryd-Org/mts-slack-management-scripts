from data_models.base import BaseSlackModel


class Workspace(BaseSlackModel):
    @property
    def db_collection(self) -> str:
        return "workspaces"
