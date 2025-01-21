import hashlib

from pydantic import BaseModel


class BaseSlackModel(BaseModel):
    slack_id: str | None = None
    name: str

    @property
    def of_type(self) -> str:
        raise NotImplementedError

    def __hash__(self):
        bytes_obj = self.slack_id.encode("utf-8")

        # Create an MD5 hash object
        md5_hash = hashlib.md5(bytes_obj)

        # Get the digest as an integer
        digest_int = int.from_bytes(md5_hash.digest(), byteorder="big", signed=False)

        return digest_int
