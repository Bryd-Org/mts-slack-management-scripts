from pydantic import BaseModel


class InstructionEntry(BaseModel):
    workspace_name: str
    workspace_slack_id: str
    channel_name: str
    channel_slack_id: str
    user_name: str
    user_slack_id: str
