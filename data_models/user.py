from data_models.base import BaseSlackModel


class User(BaseSlackModel):
    email: str
    title: str | None = None
    section: str | None = None
    extention: str | int | None = None
    location: str | None = None

    @property
    def db_collection(self) -> str:
        return "users"
