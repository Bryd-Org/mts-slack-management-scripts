from pydantic import BaseModel

from data_models.workspace_role import WorkspaceRole


class AddUserInstructionEntry(BaseModel):
    workspace_name: str
    workspace_slack_id: str
    channel_name: str
    channel_slack_id: str
    user_email: str
    user_slack_id: str


class AssignAdminOwnerInstructionEntry(BaseModel):
    workspace_name: str
    workspace_slack_id: str
    user_email: str
    user_slack_id: str
    role: WorkspaceRole


class DeactivateRemoveUserInstructionEntry(BaseModel):
    user_email: str
    user_slack_id: str


class InviteNewUserInstructionEntry(BaseModel):
    workspace_name: str
    workspace_slack_id: str
    channel_name: str
    channel_slack_id: str
    user_email: str
    user_name: str
    title: str = None
    section: str = None
    location: str = None
