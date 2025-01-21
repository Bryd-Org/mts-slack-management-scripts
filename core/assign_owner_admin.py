from data_models.instruction_entries import AssignAdminOwnerInstructionEntry
from utils.config import log
from utils.csv_manager import CSVInstructionManager
from utils.slack_connector import SlackConnectionManager


async def assign_owner_admin_processor(
    slack_data_manager: SlackConnectionManager,
    instructions: CSVInstructionManager,
):
    processed_user_ids = set()

    function_mapping = {
        "owner": slack_data_manager.make_user_owner,
        "admin": slack_data_manager.make_user_admin,
    }

    for entry in instructions.yield_assign_admin_owner_instructions():
        if entry.user_slack_id in processed_user_ids:
            log.error(f"User {entry.user_email} has already been processed!")
            continue
        log.info(f"Assigning role '{entry.role}' to user '{entry.user_email}'")
        try:
            await function_mapping[entry.role](
                user_id=entry.user_slack_id,
                workspace_id=entry.workspace_slack_id,
            )
        except Exception as e:
            log.exception(
                f"Failed to add role '{entry.role}' to user '{entry.user_slack_id}' "
                f"in workspace '{entry.workspace_slack_id}': {e}"
            )
        else:
            processed_user_ids.add(entry.user_slack_id)
