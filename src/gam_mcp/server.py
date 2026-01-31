"""
GAM MCP Server

Provides tools for managing Google Workspace via GAM7 commands.
Run this server and connect it to Claude Code to manage your domains.
"""
import subprocess
import shlex
from typing import Optional
from datetime import date, timedelta

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("gam")

# =============================================================================
# REFERENCE DATA
# =============================================================================

VALID_USER_FIELDS = [
    "addresses", "agreedtoterms", "aliases", "archived", "changepasswordatnextlogin",
    "creationtime", "customerid", "deletiontime", "displayname", "email", "employeeid",
    "externalids", "familyname", "fullname", "gender", "givenname", "id", "ims",
    "includeinglobaladdresslist", "ipwhitelisted", "isdelegatedadmin", "isenforcedin2sv",
    "isenrolledin2sv", "ismailboxsetup", "keywords", "languages", "lastlogintime",
    "locations", "manager", "name", "noneditablealiases", "notes", "organizations",
    "orgunitpath", "phones", "posixaccounts", "primaryemail", "recoveryemail",
    "recoveryphone", "relations", "sshpublickeys", "suspended", "thumbnailphotourl",
    "websites"
]

COMMON_USER_FIELDS = "primaryemail,fullname,suspended,lastlogintime,orgunitpath"


def run_gam_command(command: str, timeout: int = 300) -> dict:
    """Execute a GAM command and return the result."""
    args = shlex.split(command)
    if args and args[0].lower() != "gam":
        args = ["gam"] + args

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "GAM not found. Ensure GAMADV-XTD3 is installed and in PATH.",
            "exit_code": -1,
        }


def format_result(result: dict) -> str:
    """Format a GAM command result for display."""
    if result["success"]:
        return result["output"] or "Command completed successfully."
    return f"Error (exit {result['exit_code']}): {result['error']}"


# =============================================================================
# RESOURCES - Reference documentation Claude can read
# =============================================================================

@mcp.resource("gam://reference/user-fields")
def get_user_fields_reference() -> str:
    """List of all valid user fields for GAM print users command."""
    return f"""# Valid User Fields for GAM

Use these fields with `gam print users fields <field1,field2,...>`

## All Valid Fields
{', '.join(VALID_USER_FIELDS)}

## Common Field Combinations
- Basic: primaryemail,fullname,suspended
- Login audit: primaryemail,fullname,lastlogintime,creationtime
- Security: primaryemail,isenrolledin2sv,isenforcedin2sv,suspended
- Organization: primaryemail,fullname,orgunitpath,manager
- Contact: primaryemail,fullname,phones,recoveryemail,recoveryphone

## Query Examples
- Suspended users: `gam print users issuspended true`
- Users in OU: `gam print users query "orgUnitPath='/Sales'"`
- Inactive (90+ days): `gam print users query "lastLoginTime<{(date.today() - timedelta(days=90)).isoformat()}"`
- By name: `gam print users query "givenname:John"` or `query "familyname:Smith"`
"""


@mcp.resource("gam://reference/commands")
def get_commands_reference() -> str:
    """GAM command reference guide."""
    return """# GAM7 Command Reference

## User Management
- `gam print users` - List all users (add `fields X,Y,Z` for specific fields)
- `gam print users issuspended true` - List only suspended users
- `gam print users query "orgUnitPath='/Sales'"` - Users in specific OU
- `gam info user <email>` - Detailed info for one user
- `gam create user <email> firstname <first> lastname <last> password random` - Create user
- `gam update user <email> suspended on` - Suspend user
- `gam update user <email> suspended off` - Unsuspend user
- `gam update user <email> password random` - Reset password
- `gam update user <email> password random notify <admin@domain>` - Reset and email new password
- `gam update user <email> org "/New/OU/Path"` - Move user to OU
- `gam delete user <email>` - DELETE user (DESTRUCTIVE!)

## Security Actions (DESTRUCTIVE - cannot be undone!)
- `gam user <email> signout` - Sign out all sessions immediately
- `gam user <email> deprovision` - Revoke all OAuth tokens and app passwords
- `gam user <email> turnoff2sv` - Disable 2-step verification

## Group Management
- `gam print groups` - List all groups
- `gam print groups fields email,name,directmemberscount` - Groups with member counts
- `gam info group <group@domain>` - Group details
- `gam print group-members group <group@domain>` - List members
- `gam create group <group@domain> name "Display Name"` - Create group
- `gam update group <group@domain> add member <user@domain>` - Add member
- `gam update group <group@domain> add manager <user@domain>` - Add as manager
- `gam update group <group@domain> add owner <user@domain>` - Add as owner
- `gam update group <group@domain> remove member <user@domain>` - Remove member

## Organizational Units
- `gam print orgs` - List all OUs
- `gam create org "/Parent/Child"` - Create OU
- `gam info org "/OU/Path"` - OU details

## Common Workflows

### User Offboarding (Termination)
1. `gam user <email> signout` - End all sessions
2. `gam user <email> deprovision` - Revoke tokens
3. `gam update user <email> suspended on` - Suspend account

### Find Inactive Users
`gam print users query "lastLoginTime<YYYY-MM-DD" fields primaryemail,fullname,lastlogintime`

### Bulk Operations
GAM supports batch operations. For multiple users, you can:
- Use CSV input: `gam csv users.csv gam update user ~primaryEmail suspended on`
- Or run individual commands for each user
"""


@mcp.resource("gam://reference/workflows")
def get_workflows_reference() -> str:
    """Common GAM workflow patterns."""
    return """# Common GAM Workflows

## User Onboarding
1. Create user: `gam create user new@domain.com firstname "John" lastname "Doe" password random org "/Staff"`
2. Add to groups: `gam update group team@domain.com add member new@domain.com`
3. (Optional) Send welcome email with password

## User Offboarding (Secure Termination)
Execute in order for security:
1. `gam user leaving@domain.com signout` - Immediately end all active sessions
2. `gam user leaving@domain.com deprovision` - Revoke all OAuth tokens, app passwords
3. `gam update user leaving@domain.com suspended on` - Suspend the account
4. (Optional) `gam update user leaving@domain.com org "/Terminated"` - Move to terminated OU

## Security Incident Response
If an account is compromised:
1. `gam user compromised@domain.com signout` - Kill all sessions NOW
2. `gam user compromised@domain.com deprovision` - Revoke all tokens
3. `gam update user compromised@domain.com password random` - Force password reset
4. Review: `gam user compromised@domain.com show tokens` - Check what was authorized

## Audit: Find Inactive Users
```
gam print users query "lastLoginTime<YYYY-MM-DD" fields primaryemail,fullname,lastlogintime,suspended
```
Replace YYYY-MM-DD with target date (e.g., 90 days ago)

## Audit: Users Without 2FA
```
gam print users query "isEnrolledIn2Sv=false" fields primaryemail,fullname,isenrolledin2sv
```

## Bulk Password Reset
For a list of users, reset each password:
```
gam update user user1@domain.com password random
gam update user user2@domain.com password random
...
```
Or with CSV: `gam csv users.csv gam update user ~primaryEmail password random`
"""


# =============================================================================
# USER MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def list_users(
    fields: Optional[str] = None,
    query: Optional[str] = None,
    suspended_only: bool = False,
    active_only: bool = False,
    ou: Optional[str] = None,
    max_results: Optional[int] = None,
    inactive_days: Optional[int] = None,
) -> str:
    """List users in the Google Workspace domain with flexible filtering.

    Args:
        fields: Comma-separated fields (default: primaryemail,fullname,suspended,lastlogintime,orgunitpath).
                Common fields: primaryemail, fullname, suspended, lastlogintime, orgunitpath,
                creationtime, isenrolledin2sv, manager, recoveryemail
        query: Advanced filter query (e.g., "givenname:John", "orgUnitPath='/Sales'")
        suspended_only: If True, show only suspended users
        active_only: If True, show only non-suspended users
        ou: Filter to specific organizational unit path (e.g., "/Sales")
        max_results: Maximum number of users to return
        inactive_days: Show users who haven't logged in for this many days

    Returns:
        CSV-formatted list of users matching the criteria
    """
    cmd = "gam print users"

    # Default fields if not specified
    if fields:
        cmd += f" fields {fields}"
    else:
        cmd += f" fields {COMMON_USER_FIELDS}"

    # Handle suspension filters
    if suspended_only:
        cmd += " issuspended true"
    elif active_only:
        cmd += " issuspended false"

    # Handle OU filter
    if ou:
        cmd += f" limittoou \"{ou}\""

    # Handle inactive days filter
    if inactive_days:
        cutoff_date = (date.today() - timedelta(days=inactive_days)).isoformat()
        if query:
            query += f" lastLoginTime<{cutoff_date}"
        else:
            query = f"lastLoginTime<{cutoff_date}"

    # Add custom query
    if query:
        cmd += f' query "{query}"'

    if max_results:
        cmd += f" maxresults {max_results}"

    result = run_gam_command(cmd)
    return format_result(result)


@mcp.tool()
def get_user_info(email: str) -> str:
    """Get comprehensive information about a specific user.

    Args:
        email: The user's full email address (e.g., user@domain.com)

    Returns:
        Detailed user information including name, status, groups, aliases, etc.
    """
    result = run_gam_command(f"gam info user {email}")
    return format_result(result)


@mcp.tool()
def search_users(name: str) -> str:
    """Search for users by first or last name.

    Args:
        name: Name to search for (searches both first and last name)

    Returns:
        Users matching the name search
    """
    # Search both given name and family name
    cmd = f'gam print users query "name:{name}" fields {COMMON_USER_FIELDS}'
    result = run_gam_command(cmd)
    return format_result(result)


@mcp.tool()
def create_user(
    email: str,
    first_name: str,
    last_name: str,
    password: Optional[str] = None,
    org_unit: Optional[str] = None,
    recovery_email: Optional[str] = None,
) -> str:
    """Create a new user in Google Workspace.

    Args:
        email: The new user's email address (must be valid for your domain)
        first_name: User's first/given name
        last_name: User's last/family name
        password: Initial password (uses random secure password if not specified)
        org_unit: Organizational unit path (e.g., "/Staff" or "/Sales/West")
        recovery_email: Recovery email for password resets

    Returns:
        Result of user creation including any generated password
    """
    pwd = password or "random"
    cmd = f'gam create user {email} firstname "{first_name}" lastname "{last_name}" password {pwd}'

    if org_unit:
        cmd += f' org "{org_unit}"'
    if recovery_email:
        cmd += f' recoveryemail {recovery_email}'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"User {email} created successfully.\n{result['output']}"
    return f"Error creating user: {result['error']}"


@mcp.tool()
def update_user(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    org_unit: Optional[str] = None,
    recovery_email: Optional[str] = None,
    recovery_phone: Optional[str] = None,
) -> str:
    """Update user attributes.

    Args:
        email: The user's email address
        first_name: New first name (optional)
        last_name: New last name (optional)
        org_unit: New organizational unit path (optional)
        recovery_email: New recovery email (optional)
        recovery_phone: New recovery phone (optional)

    Returns:
        Result of the update
    """
    cmd = f"gam update user {email}"

    if first_name:
        cmd += f' firstname "{first_name}"'
    if last_name:
        cmd += f' lastname "{last_name}"'
    if org_unit:
        cmd += f' org "{org_unit}"'
    if recovery_email:
        cmd += f' recoveryemail {recovery_email}'
    if recovery_phone:
        cmd += f' recoveryphone {recovery_phone}'

    if cmd == f"gam update user {email}":
        return "Error: No attributes specified to update."

    result = run_gam_command(cmd)
    return format_result(result)


@mcp.tool()
def suspend_user(email: str) -> str:
    """Suspend a user account, preventing login but preserving data.

    Args:
        email: The user's email address

    Returns:
        Confirmation of suspension
    """
    result = run_gam_command(f"gam update user {email} suspended on")
    if result["success"]:
        return f"User {email} has been suspended. They can no longer sign in."
    return f"Error suspending user: {result['error']}"


@mcp.tool()
def unsuspend_user(email: str) -> str:
    """Reactivate a suspended user account.

    Args:
        email: The user's email address

    Returns:
        Confirmation of reactivation
    """
    result = run_gam_command(f"gam update user {email} suspended off")
    if result["success"]:
        return f"User {email} has been reactivated and can now sign in."
    return f"Error reactivating user: {result['error']}"


@mcp.tool()
def reset_password(
    email: str,
    new_password: Optional[str] = None,
    notify_email: Optional[str] = None,
    require_change: bool = True,
) -> str:
    """Reset a user's password.

    Args:
        email: The user's email address
        new_password: Specific password to set (uses secure random if not specified)
        notify_email: Email address to send the new password to
        require_change: Force user to change password on next login (default: True)

    Returns:
        Result of password reset
    """
    pwd = new_password or "random"
    cmd = f"gam update user {email} password {pwd}"

    if notify_email:
        cmd += f" notify {notify_email}"
    if require_change:
        cmd += " changepassword on"

    result = run_gam_command(cmd)
    if result["success"]:
        msg = f"Password reset for {email}."
        if require_change:
            msg += " User must change password on next login."
        if result["output"]:
            msg += f"\n{result['output']}"
        return msg
    return f"Error resetting password: {result['error']}"


@mcp.tool()
def delete_user(email: str, confirm: bool = False) -> str:
    """DELETE a user account. THIS IS DESTRUCTIVE AND CANNOT BE UNDONE!

    Args:
        email: The user's email address
        confirm: Must be True to actually delete (safety check)

    Returns:
        Result of deletion
    """
    if not confirm:
        return f"SAFETY CHECK: To delete {email}, call this tool again with confirm=True. This action CANNOT be undone!"

    result = run_gam_command(f"gam delete user {email}")
    if result["success"]:
        return f"User {email} has been DELETED. This cannot be undone."
    return f"Error deleting user: {result['error']}"


# =============================================================================
# SECURITY TOOLS
# =============================================================================

@mcp.tool()
def sign_out_user(email: str) -> str:
    """Immediately sign out a user from ALL sessions. Use for security incidents.

    This is DESTRUCTIVE - the user will be logged out of all devices immediately.
    Cannot be undone (they just need to sign in again).

    Args:
        email: The user's email address

    Returns:
        Confirmation of sign out
    """
    result = run_gam_command(f"gam user {email} signout")
    if result["success"]:
        return f"User {email} has been signed out from ALL sessions immediately."
    return f"Error signing out user: {result['error']}"


@mcp.tool()
def revoke_tokens(email: str) -> str:
    """Revoke all OAuth tokens and app passwords for a user. Use for security incidents.

    This is DESTRUCTIVE - all third-party app access will be revoked.
    The user will need to re-authorize any apps they use.

    Args:
        email: The user's email address

    Returns:
        Confirmation of token revocation
    """
    result = run_gam_command(f"gam user {email} deprovision")
    if result["success"]:
        return f"All OAuth tokens and app passwords revoked for {email}. They will need to re-authorize apps."
    return f"Error revoking tokens: {result['error']}"


@mcp.tool()
def offboard_user(email: str, confirm: bool = False) -> str:
    """Complete secure offboarding: sign out, revoke tokens, and suspend.

    This performs the standard security offboarding workflow:
    1. Sign out all sessions (immediate)
    2. Revoke all OAuth tokens and app passwords
    3. Suspend the account

    Args:
        email: The user's email address
        confirm: Must be True to proceed (safety check)

    Returns:
        Results of each step
    """
    if not confirm:
        return f"""OFFBOARDING PREVIEW for {email}:
1. Sign out all active sessions
2. Revoke all OAuth tokens and app passwords
3. Suspend the account

To proceed, call offboard_user with confirm=True"""

    results = []

    # Step 1: Sign out
    r1 = run_gam_command(f"gam user {email} signout")
    results.append(f"1. Sign out: {'Success' if r1['success'] else 'FAILED - ' + str(r1['error'])}")

    # Step 2: Deprovision
    r2 = run_gam_command(f"gam user {email} deprovision")
    results.append(f"2. Revoke tokens: {'Success' if r2['success'] else 'FAILED - ' + str(r2['error'])}")

    # Step 3: Suspend
    r3 = run_gam_command(f"gam update user {email} suspended on")
    results.append(f"3. Suspend: {'Success' if r3['success'] else 'FAILED - ' + str(r3['error'])}")

    return f"Offboarding complete for {email}:\n" + "\n".join(results)


@mcp.tool()
def check_2fa_status(email: Optional[str] = None) -> str:
    """Check 2-factor authentication enrollment status.

    Args:
        email: Specific user to check (if None, lists all users without 2FA)

    Returns:
        2FA status for the user(s)
    """
    if email:
        result = run_gam_command(f"gam info user {email}")
        return format_result(result)
    else:
        # List users not enrolled in 2FA
        cmd = 'gam print users query "isEnrolledIn2Sv=false" fields primaryemail,fullname,isenrolledin2sv'
        result = run_gam_command(cmd)
        return format_result(result)


# =============================================================================
# GROUP MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def list_groups(
    fields: Optional[str] = None,
    query: Optional[str] = None,
    max_results: Optional[int] = None,
) -> str:
    """List all groups in the domain.

    Args:
        fields: Comma-separated fields (default: email,name,directmemberscount)
        query: Filter query
        max_results: Maximum number to return

    Returns:
        CSV-formatted list of groups
    """
    cmd = "gam print groups"
    if fields:
        cmd += f" fields {fields}"
    else:
        cmd += " fields email,name,directmemberscount"
    if query:
        cmd += f' query "{query}"'
    if max_results:
        cmd += f" maxresults {max_results}"

    result = run_gam_command(cmd)
    return format_result(result)


@mcp.tool()
def get_group_info(group_email: str) -> str:
    """Get detailed information about a group including settings.

    Args:
        group_email: The group's email address

    Returns:
        Detailed group information
    """
    result = run_gam_command(f"gam info group {group_email}")
    return format_result(result)


@mcp.tool()
def list_group_members(group_email: str) -> str:
    """List all members of a group with their roles.

    Args:
        group_email: The group's email address

    Returns:
        List of group members with email and role
    """
    result = run_gam_command(f"gam print group-members group {group_email}")
    return format_result(result)


@mcp.tool()
def add_group_member(
    group_email: str,
    member_email: str,
    role: str = "MEMBER"
) -> str:
    """Add a member to a group.

    Args:
        group_email: The group's email address
        member_email: The email of the user/group to add
        role: Role in the group: MEMBER, MANAGER, or OWNER

    Returns:
        Confirmation of addition
    """
    role = role.upper()
    if role not in ["MEMBER", "MANAGER", "OWNER"]:
        return f"Invalid role '{role}'. Must be MEMBER, MANAGER, or OWNER."

    result = run_gam_command(f"gam update group {group_email} add {role.lower()} {member_email}")
    if result["success"]:
        return f"Added {member_email} to {group_email} as {role}."
    return f"Error adding member: {result['error']}"


@mcp.tool()
def remove_group_member(group_email: str, member_email: str) -> str:
    """Remove a member from a group.

    Args:
        group_email: The group's email address
        member_email: The email of the member to remove

    Returns:
        Confirmation of removal
    """
    result = run_gam_command(f"gam update group {group_email} remove member {member_email}")
    if result["success"]:
        return f"Removed {member_email} from {group_email}."
    return f"Error removing member: {result['error']}"


@mcp.tool()
def create_group(
    email: str,
    name: str,
    description: Optional[str] = None
) -> str:
    """Create a new group.

    Args:
        email: The new group's email address
        name: Display name for the group
        description: Optional description of the group's purpose

    Returns:
        Confirmation of group creation
    """
    cmd = f'gam create group {email} name "{name}"'
    if description:
        cmd += f' description "{description}"'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"Group {email} ({name}) created successfully."
    return f"Error creating group: {result['error']}"


# =============================================================================
# ORGANIZATIONAL UNIT TOOLS
# =============================================================================

@mcp.tool()
def list_org_units() -> str:
    """List all organizational units in the domain hierarchy.

    Returns:
        List of all OUs with their paths
    """
    result = run_gam_command("gam print orgs")
    return format_result(result)


@mcp.tool()
def get_org_unit_info(ou_path: str) -> str:
    """Get information about a specific organizational unit.

    Args:
        ou_path: The OU path (e.g., "/Sales" or "/Staff/Engineering")

    Returns:
        OU details
    """
    result = run_gam_command(f'gam info org "{ou_path}"')
    return format_result(result)


@mcp.tool()
def create_org_unit(
    path: str,
    description: Optional[str] = None,
    parent_ou: Optional[str] = None,
) -> str:
    """Create a new organizational unit.

    Args:
        path: The OU name or full path (e.g., "West Coast" or "/Sales/West Coast")
        description: Optional description of the OU
        parent_ou: Parent OU path if creating nested OU

    Returns:
        Confirmation of OU creation
    """
    if parent_ou and not path.startswith("/"):
        full_path = f"{parent_ou}/{path}"
    else:
        full_path = path

    cmd = f'gam create org "{full_path}"'
    if description:
        cmd += f' description "{description}"'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"Organizational unit '{full_path}' created successfully."
    return f"Error creating OU: {result['error']}"


@mcp.tool()
def list_ou_users(ou_path: str, recursive: bool = True) -> str:
    """List all users in an organizational unit.

    Args:
        ou_path: The OU path (e.g., "/Sales")
        recursive: Include users in sub-OUs (default: True)

    Returns:
        Users in the OU
    """
    if recursive:
        cmd = f'gam print users query "orgUnitPath=\'{ou_path}\'" fields {COMMON_USER_FIELDS}'
    else:
        cmd = f'gam print users limittoou "{ou_path}" fields {COMMON_USER_FIELDS}'

    result = run_gam_command(cmd)
    return format_result(result)


# =============================================================================
# RAW COMMAND TOOL (for advanced users)
# =============================================================================

@mcp.tool()
def run_gam(command: str) -> str:
    """Execute any GAM command directly. For advanced users who know GAM syntax.

    Args:
        command: The full GAM command (with or without 'gam' prefix)
                 Examples:
                 - "print users fields primaryemail,fullname"
                 - "gam info domain"
                 - "user someone@domain.com show tokens"

    Returns:
        Command output or error message
    """
    result = run_gam_command(command)
    return format_result(result)


# =============================================================================
# PROMPTS - Pre-built workflows
# =============================================================================

@mcp.prompt()
def audit_inactive_users() -> str:
    """Generate a report of users who haven't logged in recently."""
    return """Please help me audit inactive users in my Google Workspace domain.

1. First, list users who haven't logged in for 90 days
2. Summarize how many inactive users there are
3. Ask if I want to take any action on them (like suspension)"""


@mcp.prompt()
def security_audit() -> str:
    """Run a security audit of the domain."""
    return """Please run a security audit of my Google Workspace domain:

1. Check for users without 2FA enabled
2. List any suspended users
3. Identify users with admin privileges
4. Summarize findings with recommendations"""


@mcp.prompt()
def new_employee_onboarding() -> str:
    """Onboard a new employee."""
    return """I need to onboard a new employee. Please help me:

1. Ask for the new employee's details (name, email, department)
2. Create their user account
3. Add them to appropriate groups based on their department
4. Summarize what was set up"""


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
