# mts-slack-management-scripts

## Installing a Slack App and configuring token

### **Prerequisites**
- You need admin privileges in your Slack workspace to perform the steps.

### **Step 1: Create a Slack App**
1. Go to the [Slack API Dashboard](https://api.slack.com/apps) and click **Create an App**.
2. Choose **From manifest**.
3. Select a workspace in your Enterprise Grid.
4. Copy-paste app manifest from `slack_app_manifest.json` file.
5. Click **Create**.

### **Step 2: Install the App with Org-Wide Opt-In**
1. In the **Settings** section, scroll to the **Install App** section.
2. Click **Install to Organization**.
3. Authorize the app with the required permissions.

### **Step 3: Acquire the Admin Token**
1. Navigate to the **OAuth & Permissions** section of your app.
2. After installation, copy the **User OAuth Token**.

### **Step 4: Set Token into this App**
1. Create `.secrets.toml` in this repository.
2. Insert these lines into secrets file, replacing `YOUR_TOKEN` with valid slack **User OAuth Token**.
   ```toml
   [default]
   SLACK_USER_TOKEN = "YOUR_TOKEN"
   ```

### **Common Issues**
- **Invalid Token**: Confirm you’re using the correct token from the **OAuth & Permissions** section.
- **Org-Wide Opt-In Failure**: Verify that the app is installed at the organization level and not just a single workspace.

---

### **How to Acquire a Workspace ID**

1. **Navigate to Organization Settings**  
   - Open your **Slack**.  
   - Go to **Organization Settings**.

2. **Find the Workspaces Section**  
   - In the settings menu, click on **Workspaces** to see the list of all workspaces in your organization.

3. **Copy the Workspace ID**  
   - Locate the workspace for which you need the ID.  
   - Click on the **three dots menu** (⋮) next to the workspace name.  
   - Select **Copy Workspace ID** from the dropdown menu.

You can now use this workspace ID in the instructions file.

---

### **How to Acquire a Slack Channel ID**

1. **Open Slack**  
   - Launch your **Slack** application.

2. **Navigate to the Channel**  
   - Click on the channel for which you need the ID in the sidebar to open it.

3. **Access Channel Details**  
   - Click on the **channel name** at the top of the conversation to open the channel details pane.

4. **Copy the Channel ID**
   - Click on the **More** options (⋮) in the channel details pane, scroll down and select **Copy ID**.  
   It usually starts with a `C` or `G` followed by a series of letters and numbers.
   
You can now use this channel ID in the instructions file.

---

### **How to Acquire a Slack User ID**

1. **Open Admin Web Console**  
   - Open admin web console.
   - Go to **People** - **Members** page

2. **Find the User**
   - Search for the user in the search bar.
   - Click on the user's name to open the user's profile page.

3. **Copy the User ID**
   - In address bar of the browser find the user ID after `/people/`.
   It usually starts with a `U` followed by a series of letters and numbers.

You can now use this user ID in the instructions file.

---

### **Script container testing** (*test*)

All the scripts here are run as linux docker containers. To verify that you operating system is able to run 
them you might use this test command. No additional preparation required.

   
1. **Run process**  
   - Execute the following command to assign admin or owner role:
     ```bash
     docker-compose up test
     ```

**Result:**

After container assembly it should log that script is starting, then working and sleeping 5 seconds and then 
correct exit with code 0.

Correct log example:
```log
test-1  | [2025-01-21 09:40:00,674][INFO] main.py:98 | Script starting
test-1  | [2025-01-21 09:40:00,676][INFO] main.py:87 | Script self test is working. Sleeping 5 seconds
test-1  | [2025-01-21 09:40:05,679][INFO] main.py:89 | Script self test finished
test-1 exited with code 0

```

---

### **Add users to workspaces and channels** (*add-users*)

1. **Prepare the instructions file**  
   - Open the `add_users_instruction.csv` file.  
   - Populate it with `workspace_name`, `workspace_slack_id`, `channel_name`, `channel_slack_id`, `user_name`, `user_slack_id`. 
   Each line is a relation between workspace-channel-user. A single user can have several lines
   which denote several channels user would be added to.

2. **Run process**  
   - Execute the following command to add users to channels and workspaces:
     ```bash
     docker-compose up add-users
     ```

**Result:**  

After execution, users which are not members of the workspace (or deactivated) would be invited to join workspace and 
assigned to channels from `add_users_instruction.csv` file.

---


### **Assign users as workspace owners and admins** (*assign-admins*)

1. **Prepare the instructions file**  
   - Open the `assign_user_admin_instruction.csv` file.  
   - Populate it with `workspace_name`, `workspace_slack_id`, `user_name`, `user_slack_id,role`. 
   Each line is a meant for a single user. User role should be in lowercase: `admin` or `owner`.
   
2. **Run process**  
   - Execute the following command to assign admin or owner role:
     ```bash
     docker-compose up assign-admins
     ```

**Result:**  


After execution users from `assign_user_admin_instruction.csv` file would be assigned corresponding roles in their workspace.

---

### **Invite new users to workspaces** (*invite-new-users*)

This script would create new users in slack and invite them to workspace from `invite_new_user_instruction.csv` file.
Currently existing users would be ignored, as this would violate the purpose of the script - 
create new user and trigger invitation email. If you need to invite existing users, use `invite_new_user_instruction.csv` file.

1. **Prepare the instructions file**  
   - Open the `invite_new_user_instruction.csv` file.  
   - Populate it with `workspace_name`, `workspace_slack_id`, `channel_name`, `channel_slack_id`, `user_email`, 
`user_name`, `title`, `section`, `location` values.
   - Each line is a relation between workspace-channel-user. A single user can have several lines
   which denote several channels user would be added to.
   
2. **Run process**  
   - Execute the following command to invite new users to slack:
   - **All currently active users would be ignored!**
     ```bash
     docker-compose up invite-new-users
     ```

**Result:**  


After execution users from `invite_new_user_instruction.csv` file would be created and assigned to corresponding channels.
Also user data would be filled from `invite_new_user_instruction.csv` file. 

---

### **Unassign email from user** (*change-deactivated-emails*)

This script would change email address of deactivated user to a new and invalid one. 
This is done for the purpose of creating a new account for this user and invite this account to workspace.
Alternative to it - is account deletion, however it could be only done automatically.

1. **Prepare the instructions file**  
   - Open the `change_deactivated_user_email_instruction.csv` file.  
   - Populate it with `user_email` and `user_slack_id` values.
   - Each line is a meant for a single user.
   
2. **Run process**  
   - Execute the following command to unassign deactivated user email:
   - **All active users would be ignored!**
     ```bash
     docker-compose up change-deactivated-emails
     ```

**Result:**

After execution users' accounts from instruction file would be changed and marked as deactivated.
