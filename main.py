import asyncio

import typer

from core.activate_users_add_to_channels import add_users_to_ws_channels
from core.assign_owner_admin import assign_owner_admin
from utils.config import settings as s, log
from utils.csv_manager import CSVInstructionManager
from utils.slack_connector import SlackConnectionManager

app = typer.Typer()


@app.command(name="add-users")
def add_users():
    # creating slack data manager to connect to slack API
    slack_data_manager = SlackConnectionManager(s.SLACK_USER_TOKEN)

    # dict to hold information on users to be processed

    # reading instructions from csv
    instructions = CSVInstructionManager(filename="add_users_instruction.csv")

    asyncio.run(
        add_users_to_ws_channels(
            slack_data_manager=slack_data_manager, instructions=instructions
        )
    )


@app.command(name="assign-admins")
def assign_admins():
    # creating slack data manager to connect to slack API
    slack_data_manager = SlackConnectionManager(s.SLACK_USER_TOKEN)

    # dict to hold information on users to be processed

    # reading instructions from csv
    instructions = CSVInstructionManager(filename="assign_user_admin_instruction.csv")

    asyncio.run(
        assign_owner_admin(
            slack_data_manager=slack_data_manager, instructions=instructions
        )
    )


if __name__ == "__main__":
    log.info("Script starting")
    app()
    log.info("Script finished")
