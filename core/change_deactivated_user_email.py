import hashlib
from datetime import datetime

from data_models.instruction_entries import DeactivateRemoveUserInstructionEntry
from utils.config import log
from utils.csv_manager import CSVInstructionManager
from utils.slack_connector import SlackConnectionManager, UserIsActiveError


async def change_deactivated_users_email_processor(
    slack_data_manager: SlackConnectionManager,
    instructions: CSVInstructionManager,
):
    total = instructions.total_instructions
    current = 0

    for entry in instructions.yield_deactivate_remove_user_instructions():
        entry: DeactivateRemoveUserInstructionEntry
        current += 1
        log.info(
            f"({current}/{total}) Working on for deactivated user '{entry.user_email}'"
        )

        try:
            await slack_data_manager.verify_deactivated_user_email(entry.user_email)
        except UserIsActiveError:
            log.error(f"User '{entry.user_email}' is currently active!")
            continue
        except Exception as e:
            log.exception(
                f"Failed to verify deactivated user '{entry.user_email}': {e}"
            )
            continue

        email_address, email_domain = entry.user_email.split("@")

        # adding a bit of randomness to exclude possible collisions
        new_invalid_address_base = (
            f"{datetime.now().isoformat()}{email_address}".encode("utf-8")
        )
        deactivated_user_code = hashlib.shake_128(new_invalid_address_base).hexdigest(4)

        new_email = f"deactivated-{deactivated_user_code}@{email_domain}"

        new_scim_user = slack_data_manager.fill_scim_user(
            username=f"deactivated-{deactivated_user_code}",
            display_name="deactivated",
            email=new_email,
            id=entry.user_slack_id,
        )

        try:
            await slack_data_manager.update_user(user_data=new_scim_user)
        except Exception as e:
            log.exception(
                f"Failed to change email for user '{entry.user_slack_id}': {e}"
            )
        else:
            log.info(
                f"Changed email for deactivated user '{entry.user_email}' to '{new_email}'"
            )
