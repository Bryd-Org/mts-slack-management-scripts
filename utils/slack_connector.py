import asyncio
import re
from datetime import datetime, UTC

from slack_sdk import WebClient
from slack_sdk.scim import SCIMClient, User as ScimUser

from .config import log
from data_models.channel import Channel
from data_models.user import User
from data_models.workspace import Workspace


class BadUsernameError(ValueError):
    pass


class UnknownSlackUserCreationError(ValueError):
    pass


class SlackConnectionManager:
    def __init__(self, token: str):
        if not token:
            raise ValueError("Slack Api token is required! ")

        self._slack_user_client = WebClient(token=token)
        self._scim_client = SCIMClient(token=token)
        self._debounce_data = {}

    async def _debounce(self, function_name: str, rate_limit_per_minute: int):
        """
        Debounce a Slack API call to avoid hitting rate limits.

        Args:
            function_name: name of the function to debounce
            rate_limit_per_minute: rate limit in calls per minute
        """
        if function_name not in self._debounce_data:
            self._debounce_data[function_name] = datetime.now(UTC)
            return

        current_time = datetime.now(UTC)
        time_since_last_call = current_time - self._debounce_data[function_name]
        if time_since_last_call.total_seconds() < 60 / rate_limit_per_minute:
            sleep_time = (
                (60 / rate_limit_per_minute) - time_since_last_call.total_seconds() + 1
            )
            log.info(
                f"Sleeping for {sleep_time} seconds to avoid rate limit for '{function_name}'"
            )
            await asyncio.sleep(sleep_time)

        self._debounce_data[function_name] = current_time

    @staticmethod
    def _create_scim_user(
        username: str,
        display_name: str,
        email: str,
        title: str,
        location: str,
        section: str,
    ):

        user_data = {
            "schemas": [
                "urn:scim:schemas:core:1.0",
                "urn:scim:schemas:extension:enterprise:1.0",
            ],
            "userName": username.strip(),
            "displayName": display_name.strip(),
            "title": title,
            "emails": [{"value": email, "primary": True}],
            "active": False,
            "unknown_fields": {
                "urn:scim:schemas:extension:enterprise:1.0": {
                    # "employeeNumber": user.extention,
                    "department": location,
                    "division": section,
                },
            },
        }

        return ScimUser(**user_data)

    async def _create_slack_user(self, scim_user: ScimUser) -> str:
        await self._debounce("create_user", 20)
        response = self._scim_client.create_user(user=scim_user)
        if response.status_code == 201:
            user_id = response.body["id"]
            # log.info(f"User {user.email} created successfully. Slack ID: {user_id}")
            return user_id
        elif response.status_code in (400, 409):
            error_type = response.errors.description.split(" ")[0]
            if error_type in (
                "username_invalid",
                "username_too_long",
                "username_taken",
            ):
                raise BadUsernameError(response.body)
        else:
            raise UnknownSlackUserCreationError(response.body)

    async def upload_new_single_user(self, user: User):
        """
        Creates a new user in Slack.

        Args:
            user: The user to create
        Returns:
            The Slack ID of the newly created user
        Raises:
            BadUsernameError: If the username is invalid
            UnknownSlackUserCreationError: If the user could not be created
        """
        existing_user_data = await self.verify_user_not_exists_in_slack(user)

        if existing_user_data:
            slack_id = existing_user_data["id"]
            log.info(
                f"User {user.get('userName')} already exists in Slack, slack_id={slack_id}"
            )
            return slack_id

        scim_user = self._create_scim_user(
            username=user.name,
            display_name=user.name,
            email=user.email,
            title=user.title,
            location=user.location,
            section=user.section,
        )
        try:
            created_user_id = await self._create_slack_user(scim_user)
        except BadUsernameError:
            # bad username - so we take what is more consistent - email username
            short_username = user.email.split("@")[0]
            log.warning(
                f"Full name is too long for user {user.email}. Using short name '{short_username}'."
            )
            new_scim_user = self._create_scim_user(
                username=short_username,
                display_name=user.name,
                email=user.email,
                title=user.title,
                location=user.location,
                section=user.section,
            )
            created_user_id = await self._create_slack_user(new_scim_user)
        except Exception as e:
            log.exception(f"Failed to create user {user.email}: {e}")
            raise e

        log.info(f"User {user.email} created successfully. Slack ID: {created_user_id}")
        return created_user_id

    async def verify_user_not_exists_in_slack(self, user: User) -> dict | None:
        """
        Verifies if a user does not exist in Slack.

        Args:
            user: The user to verify

        Returns:
            The Slack ID of the existing user if found, otherwise None

        Raises:
            Exception: If multiple users are found with the same email
        """
        await self._debounce("scim_search_users", 20)
        filter_query = f"email co {user.email}"

        response = self._scim_client.search_users(
            count=10, start_index=0, filter=filter_query
        )
        if response.status_code != 200:
            raise Exception("Failed to search users in Slack")

        existing_users = response.body.get("Resources")

        if not existing_users:
            return

        if len(existing_users) > 1:
            log.warning(f"Multiple users found with email {user.email}")
            raise Exception("Multiple users found with email")

        user = existing_users[0]

        return user

    async def deactivate_user(self, user: User):
        """
        Deactivates a Slack user by setting their 'active' status to False.
        Thus removing user from all the channel and workspaces

        Args:
            user: The user to deactivate. Must have a valid Slack ID.

        Raises:
            Exception: If the user could not be deactivated.
        """
        await self._debounce("admin_users_delete", 90)
        self._scim_client.patch_user(user.slack_id, {"active": False})

    async def verify_workspace_exists_in_slack(
        self, workspace: Workspace
    ) -> str | None:
        """
        Verifies if a workspace exists in Slack.

        Args:
            workspace: The workspace to verify.

        Returns:
            The Slack ID of the existing workspace if found, otherwise None.

        Raises:
            Exception: If the API call to list teams fails.
        """
        await self._debounce("admin_teams_list", 50)
        response = self._slack_user_client.admin_teams_list()

        if not response.data["ok"]:
            raise Exception("Failed to list teams in Slack")

        for team in response.data["teams"]:
            if team["name"] == workspace.name:
                return team["id"]

    async def create_workspace_in_slack(self, workspace: Workspace):
        """
        Creates a new workspace in Slack.

        Args:
            workspace: The workspace to create.

        Returns:
            The Slack ID of the newly created workspace.

        Raises:
            ValueError: If the domain name is too long.
            Exception: If the workspace could not be created.
        """
        existing_workspace_id = await self.verify_workspace_exists_in_slack(workspace)

        if existing_workspace_id:
            log.info(
                f"Workspace {workspace.name} already exists in Slack, slack_id={existing_workspace_id}"
            )
            return existing_workspace_id

        await self._debounce("admin_teams_create", 1)
        domain = workspace.name.lower().lstrip()

        # domains should be unique for slack platform
        # adding company abbreviation is a good way to achieve that
        domain = re.sub(r"\s+", "-", domain) + "-misr"

        # domain should be shorter that 21 characters
        # 'training-abcdefghijkl.slack.com' is the longest possible domain

        if len(domain) > 21:
            raise ValueError(
                f"Domain name '{domain}' is too long ({len(domain)} characters)"
            )
        response = self._slack_user_client.admin_teams_create(
            team_name=workspace.name,
            team_domain=domain,
        )
        if not response["ok"]:
            raise Exception("Failed to create workspace in Slack")

        workspace_id = response["team"]

        log.info(
            f"Workspace {workspace.name} created successfully. Slack ID: {workspace_id}"
        )
        return workspace_id

    async def create_channel_in_slack(self, channel: Channel, workspace: Workspace):
        """
        Creates a new channel in Slack.

        Args:
            channel: The channel to create.
            workspace: The workspace in which to create the channel.

        Returns:
            The Slack ID of the newly created channel.

        Raises:
            Exception: If the channel could not be created.
        """
        if channel.slack_id:
            log.info(f"Channel {channel.name} already has a Slack ID.")
            return channel.slack_id

        await self._debounce("conversations_create", 20)

        # using basic method (not admin) requires joining the workspace first
        created_channel = self._slack_user_client.conversations_create(
            name=channel.prepared_name,
            description=channel.description,
            team_id=workspace.slack_id,
            is_private=False,
        )
        return created_channel.data["channel"]["id"]

    async def link_channel_to_additional_workspace(
        self,
        channel: Channel,
        additional_workspaces: list[Workspace],
        main_workspace: Workspace,
    ):
        """
        Links a channel to additional workspaces in Slack.

        Args:
            channel: The channel to link.
            additional_workspaces: A list of workspaces to which the channel will be linked.
            main_workspace: The main workspace where the channel currently exists.

        Raises:
            Exception: If the channel could not be linked to additional workspaces.
        """
        await self._debounce("set_teams", 20)
        self._slack_user_client.admin_conversations_setTeams(
            channel_id=channel.slack_id,
            target_team_ids=[w.slack_id for w in additional_workspaces],
            team_id=main_workspace.slack_id,
        )

    async def add_user_to_team(
        self, user: User, workspace: Workspace, channel_slack_ids: list[str]
    ):
        """
        Adds a user to a workspace in Slack and assigns them to channels.
        This would activate user and send them a welcome message

        A wrapper for "add_user_to_team_by_ids"

        Args:
            user: The user to add.
            workspace: The workspace to add the user to.
            channel_slack_ids: A list of channel IDs to which the user will be assigned.

        Raises:
            Exception: If the user could not be added to the workspace.
        """
        await self.add_user_to_team_by_ids(
            user_id=user.slack_id,
            workspace_id=workspace.slack_id,
            channel_slack_ids=channel_slack_ids,
        )

    async def add_user_to_team_by_ids(
        self, user_id: str, workspace_id: str, channel_slack_ids: list[str]
    ):
        """
        Adds a user to a workspace in Slack by IDs and assigns them to channels.
        This would activate user and send them a welcome message

        Args:
            user_id: The Slack ID of the user to add.
            workspace_id: The Slack ID of the workspace to add the user to.
            channel_slack_ids: A list of channel IDs to which the user will be assigned.

        Raises:
            Exception: If the user could not be added to the workspace.
        """
        await self._debounce("admin_users_assign", 20)
        self._slack_user_client.admin_users_assign(
            team_id=workspace_id,
            user_id=user_id,
            channel_ids=channel_slack_ids,
        )

    async def invite_user_to_channel(self, user_id: str, channel_slack_id: str):
        """
        Invites a user to channels in a workspace in Slack by IDs.

        Args:
            user_id: The Slack ID of the user to invite.
            channel_slack_id: A list of channel IDs to which the user will be invited.

        Raises:
            Exception: If the user could not be invited to the workspace.
        """
        await self._debounce("admin_conversations_invite", 20)
        self._slack_user_client.admin_conversations_invite(
            user_ids=user_id,
            channel_ids=channel_slack_id,
        )

    async def get_users_of_workspace(
        self, workspace: Workspace, next_cursor: str = None
    ):
        """
        Retrieves a list of users from a specified Slack workspace.

        Args:
            workspace: The workspace from which to retrieve users.
            next_cursor: The cursor for pagination of the Slack API results.

        Returns:
            A list of user objects from the workspace.

        Raises:
            Exception: If the API call to list users fails.
        """
        await self._debounce("users_list", 20)
        results = self._slack_user_client.users_list(
            team_id=workspace.slack_id, limit=150, cursor=next_cursor
        )
        next_cursor = results.data["response_metadata"].get("next_cursor")

        if next_cursor:
            users = await self.get_users_of_workspace(workspace, next_cursor)
            return results.data["members"] + users

        return results.data["members"]

    async def remove_user_from_workspace(self, user: User, workspace: Workspace):
        """
        Removes a user from a workspace in Slack.

        Args:
            user: The user to remove.
            workspace: The workspace from which to remove the user.

        Raises:
            Exception: If the user could not be removed from the workspace.
        """
        await self._debounce("admin_users_remove", 20)
        self._slack_user_client.admin_users_remove(
            team_id=workspace.slack_id,
            user_id=user.slack_id,
        )

    async def make_channel_private(self, channel: Channel):
        """
        Makes a public channel private in Slack.

        Args:
            channel: The channel to make private.

        Raises:
            Exception: If the channel could not be made private.
        """
        await self._debounce("admin_conversations_convertToPrivate", 20)
        self._slack_user_client.admin_conversations_convertToPrivate(
            channel_id=channel.slack_id
        )

    async def make_user_admin(self, user_id: str, workspace_id: str):
        await self._debounce("admin_users_setAdmin", 20)
        self._slack_user_client.admin_users_setAdmin(
            team_id=workspace_id,
            user_id=user_id,
        )

    async def make_user_owner(self, user_id: str, workspace_id: str):
        await self._debounce("admin_users_setOwner", 20)
        self._slack_user_client.admin_users_setOwner(
            team_id=workspace_id,
            user_id=user_id,
        )
