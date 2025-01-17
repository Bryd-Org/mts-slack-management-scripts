from pydantic import BaseModel

from data_models.instruction_entries import AddUserInstructionEntry
from utils.config import log
from utils.csv_manager import CSVInstructionManager
from utils.slack_connector import SlackConnectionManager


class ProcessableAssignEntry(BaseModel):
    workspace_slack_id: str
    user_slack_id: str
    channels_slack_ids: list[str]

    @classmethod
    def new(cls, workspace_slack_id: str, user_slack_id: str):
        return cls(
            workspace_slack_id=workspace_slack_id,
            user_slack_id=user_slack_id,
            channels_slack_ids=[],
        )


async def add_already_active_user_to_channel(
    slack_data_manager: SlackConnectionManager,
    entry: ProcessableAssignEntry,
):
    for channel_id in entry.channels_slack_ids:
        log.info(f"Inviting user {entry.user_slack_id} to channel {channel_id}")
        await slack_data_manager.invite_user_to_channel(
            user_id=entry.user_slack_id,
            channel_slack_id=channel_id,
        )


async def add_users_to_ws_channels(
    slack_data_manager: SlackConnectionManager,
    instructions: CSVInstructionManager,
):
    log.info("Starting CSV instructions file parsing")

    data_to_work_on = {}
    for csv_entry in instructions.read_entries(AddUserInstructionEntry):
        # each line in CSV represents a user-channel relation
        # since we could add a user to multiple channel at once we need to collect all channel IDs for a single user
        key = (csv_entry.workspace_slack_id, csv_entry.user_slack_id)

        processable_entry = data_to_work_on.get(key)

        if not processable_entry:
            processable_entry = ProcessableAssignEntry.new(
                workspace_slack_id=csv_entry.workspace_slack_id,
                user_slack_id=csv_entry.user_slack_id,
            )
            data_to_work_on[key] = processable_entry

        processable_entry.channels_slack_ids.append(csv_entry.channel_slack_id)

    log.info(
        f"Found {len(data_to_work_on)} workspace-user combinations. Starting to attach users"
    )

    for entry in data_to_work_on.values():
        # Adding users to workspace one at a time
        # If user is a member of multiple channels, they would be added to all of them
        log.info(f"Adding user {entry.user_slack_id} to {entry.workspace_slack_id}")
        try:
            await slack_data_manager.add_user_to_team_by_ids(
                workspace_id=entry.workspace_slack_id,
                user_id=entry.user_slack_id,
                channel_slack_ids=entry.channels_slack_ids,
            )
        except Exception as e:
            if e.response["error"] == "user_already_team_member":
                log.warning(
                    f"Cannot add user to workspace'{entry.user_slack_id}'. "
                    f"Already a member of a workspace. Adding to channels"
                )
                try:
                    await add_already_active_user_to_channel(slack_data_manager, entry)
                except Exception as e:
                    log.exception(
                        f"Failed add user {entry.user_slack_id} to channels': {e}"
                    )
            else:
                log.exception(
                    f"Failed add user {entry.user_slack_id} in workspace '{entry.workspace_slack_id}': {e}"
                )
