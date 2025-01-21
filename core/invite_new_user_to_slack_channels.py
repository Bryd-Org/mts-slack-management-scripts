from pydantic import BaseModel

from data_models.instruction_entries import InviteNewUserInstructionEntry
from utils.config import log
from utils.csv_manager import CSVInstructionManager
from utils.slack_connector import SlackConnectionManager, UserAlreadyExistsError


class ProcessableInviteEntry(BaseModel):
    workspace_slack_id: str
    user_email: str

    scim_user_data: dict

    channels_slack_ids: list[str]

    @classmethod
    def new(cls, workspace_slack_id: str, user_email: str, scim_user_data: dict):
        return cls(
            workspace_slack_id=workspace_slack_id,
            user_email=user_email,
            scim_user_data=scim_user_data,
            channels_slack_ids=[],
        )


async def invite_new_users_processor(
    slack_data_manager: SlackConnectionManager,
    instructions: CSVInstructionManager,
):
    existing_user_emails: set[str] = set()

    data_to_work_on = {}

    for csv_entry in instructions.yield_invite_new_users_instructions():
        csv_entry: InviteNewUserInstructionEntry
        # each line in CSV represents a user-channel relation
        # since we could add a user to multiple channel at once we need to collect all channel IDs for a single user

        if csv_entry.user_email in existing_user_emails:
            # a repeated entry for a user that already exists in Slack
            continue
        try:
            await slack_data_manager.verify_user_not_exists_in_slack(
                user_email=csv_entry.user_email
            )
        except UserAlreadyExistsError:
            log.error(
                f"User '{csv_entry.user_email}' already exists in Slack! Not adding this user to channels"
            )
            existing_user_emails.add(csv_entry.user_email)
            continue

        key = (csv_entry.workspace_slack_id, csv_entry.user_email)
        processable_entry = data_to_work_on.get(key)

        if not processable_entry:
            scim_user_data = {
                "username": csv_entry.user_email.split("@")[0],
                "display_name": csv_entry.user_name,
                "email": csv_entry.user_email,
                "title": csv_entry.title,
                "location": csv_entry.location,
                "section": csv_entry.section,
            }

            processable_entry = ProcessableInviteEntry.new(
                workspace_slack_id=csv_entry.workspace_slack_id,
                user_email=csv_entry.user_email,
                scim_user_data=scim_user_data,
            )

            data_to_work_on[key] = processable_entry

        processable_entry.channels_slack_ids.append(csv_entry.channel_slack_id)

    log.info(
        f"Found {len(data_to_work_on)} workspace-user combinations. Starting to attach users"
    )

    # {email: slack_id}
    hereby_invited_users: dict[str, str] = {}
    users_to_scim_update: dict[str, dict] = {}

    for entry in data_to_work_on.values():
        if entry.user_email in hereby_invited_users:
            log.info(
                f"Adding already created user {entry.user_email} to workspace {entry.workspace_slack_id}"
            )
            # in case of a separate workspace  do not invite same user again to Slack
            # invite him to channel instead

            await slack_data_manager.add_user_to_workspace_by_ids(
                workspace_id=entry.workspace_slack_id,
                user_id=hereby_invited_users[entry.user_email],
                channel_slack_ids=entry.channels_slack_ids,
            )
        else:
            log.info(
                f"Inviting user {entry.user_email} to workspace {entry.workspace_slack_id}"
            )
            try:
                new_user_id = await slack_data_manager.invite_new_user_to_workspace(
                    user_email=entry.user_email,
                    team_id=entry.workspace_slack_id,
                    channel_ids=entry.channels_slack_ids,
                    email_password_policy_enabled=True,
                    resend_invitation_enabled=True,
                )
            except Exception as e:
                log.exception(
                    f"Slack failed to invite user '{entry.user_email}' to workspace '{entry.workspace_slack_id}': {e}"
                )
                continue
            users_to_scim_update[new_user_id] = entry.scim_user_data
            hereby_invited_users[entry.user_email] = new_user_id

    log.info(f"All users have been created and assigned to channels")
    log.info(f"Proceeding to fill SCIM data for created users")

    for user_id, scim_data in users_to_scim_update.items():
        scim_user = slack_data_manager.fill_scim_user(
            id=user_id, active=True, **scim_data
        )
        try:
            await slack_data_manager.update_user(user_data=scim_user)
        except Exception as e:
            log.exception(f"Failed to fill SCIM data for user '{user_id}': {e}")
