"""
GAM MCP Server

Provides tools for managing Google Workspace via GAM7 commands.
Run this server and connect it to Claude Code to manage your domains.
"""
import subprocess
import shlex
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("gam")


def run_gam_command(command: str, timeout: int = 300) -> dict:
    """Execute a GAM command and return the result."""
    # Parse command, ensure it starts with gam
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
            "error": "GAM not found. Ensure gam7 is installed and in PATH.",
            "exit_code": -1,
        }


# =============================================================================
# USER MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def list_users(
    fields: Optional[str] = None,
    query: Optional[str] = None,
    suspended: Optional[bool] = None,
    max_results: Optional[int] = None,
) -> str:
    """List users in the Google Workspace domain.

    Args:
        fields: Comma-separated fields to include (e.g., "primaryemail,fullname,suspended,lastlogintime")
        query: Filter query (e.g., "orgUnitPath='/Sales'" or "givenname:John")
        suspended: Filter by suspension status (True=only suspended, False=only active)
        max_results: Maximum number of users to return

    Returns:
        CSV-formatted list of users
    """
    cmd = "gam print users"

    if fields:
        cmd += f" fields {fields}"
    if query:
        cmd += f' query "{query}"'
    if suspended is not None:
        cmd += f" issuspended {'true' if suspended else 'false'}"
    if max_results:
        cmd += f" maxresults {max_results}"

    result = run_gam_command(cmd)
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def get_user_info(email: str) -> str:
    """Get detailed information about a specific user.

    Args:
        email: The user's email address

    Returns:
        Detailed user information
    """
    result = run_gam_command(f"gam info user {email}")
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def create_user(
    email: str,
    first_name: str,
    last_name: str,
    password: Optional[str] = None,
    org_unit: Optional[str] = None,
) -> str:
    """Create a new user in Google Workspace.

    Args:
        email: The new user's email address
        first_name: User's first name
        last_name: User's last name
        password: Password (uses 'random' if not specified)
        org_unit: Organizational unit path (e.g., "/Sales")

    Returns:
        Result of user creation
    """
    pwd = password or "random"
    cmd = f'gam create user {email} firstname "{first_name}" lastname "{last_name}" password {pwd}'

    if org_unit:
        cmd += f' org "{org_unit}"'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"User {email} created successfully.\n{result['output']}"
    return f"Error creating user: {result['error']}"


@mcp.tool()
def suspend_user(email: str) -> str:
    """Suspend a user account.

    Args:
        email: The user's email address

    Returns:
        Result of suspension
    """
    result = run_gam_command(f"gam update user {email} suspended on")
    if result["success"]:
        return f"User {email} has been suspended."
    return f"Error suspending user: {result['error']}"


@mcp.tool()
def unsuspend_user(email: str) -> str:
    """Reactivate a suspended user account.

    Args:
        email: The user's email address

    Returns:
        Result of reactivation
    """
    result = run_gam_command(f"gam update user {email} suspended off")
    if result["success"]:
        return f"User {email} has been reactivated."
    return f"Error reactivating user: {result['error']}"


@mcp.tool()
def reset_password(email: str, notify_email: Optional[str] = None) -> str:
    """Reset a user's password to a random value.

    Args:
        email: The user's email address
        notify_email: Email to send the new password to (optional)

    Returns:
        Result of password reset
    """
    cmd = f"gam update user {email} password random"
    if notify_email:
        cmd += f" notify {notify_email}"

    result = run_gam_command(cmd)
    if result["success"]:
        return f"Password reset for {email}.\n{result['output']}"
    return f"Error resetting password: {result['error']}"


@mcp.tool()
def move_user_to_ou(email: str, org_unit: str) -> str:
    """Move a user to a different organizational unit.

    Args:
        email: The user's email address
        org_unit: Target organizational unit path (e.g., "/Sales/West")

    Returns:
        Result of the move
    """
    result = run_gam_command(f'gam update user {email} org "{org_unit}"')
    if result["success"]:
        return f"User {email} moved to {org_unit}."
    return f"Error moving user: {result['error']}"


# =============================================================================
# SECURITY TOOLS
# =============================================================================

@mcp.tool()
def sign_out_user(email: str) -> str:
    """Sign out a user from all sessions (DESTRUCTIVE - cannot be undone).

    Args:
        email: The user's email address

    Returns:
        Result of sign out
    """
    result = run_gam_command(f"gam user {email} signout")
    if result["success"]:
        return f"User {email} has been signed out from all sessions."
    return f"Error signing out user: {result['error']}"


@mcp.tool()
def revoke_tokens(email: str) -> str:
    """Revoke all OAuth tokens and app passwords for a user (DESTRUCTIVE).

    Args:
        email: The user's email address

    Returns:
        Result of token revocation
    """
    result = run_gam_command(f"gam user {email} deprovision")
    if result["success"]:
        return f"All tokens revoked for {email}."
    return f"Error revoking tokens: {result['error']}"


# =============================================================================
# GROUP MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def list_groups(fields: Optional[str] = None) -> str:
    """List all groups in the domain.

    Args:
        fields: Comma-separated fields (e.g., "email,name,description,directmemberscount")

    Returns:
        CSV-formatted list of groups
    """
    cmd = "gam print groups"
    if fields:
        cmd += f" fields {fields}"

    result = run_gam_command(cmd)
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def get_group_info(group_email: str) -> str:
    """Get detailed information about a group.

    Args:
        group_email: The group's email address

    Returns:
        Detailed group information
    """
    result = run_gam_command(f"gam info group {group_email}")
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def list_group_members(group_email: str) -> str:
    """List all members of a group.

    Args:
        group_email: The group's email address

    Returns:
        List of group members
    """
    result = run_gam_command(f"gam print group-members group {group_email}")
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def add_group_member(group_email: str, member_email: str, role: str = "MEMBER") -> str:
    """Add a member to a group.

    Args:
        group_email: The group's email address
        member_email: The email of the user to add
        role: Member role (MEMBER, MANAGER, or OWNER)

    Returns:
        Result of adding member
    """
    result = run_gam_command(f"gam update group {group_email} add {role.lower()} {member_email}")
    if result["success"]:
        return f"Added {member_email} to {group_email} as {role}."
    return f"Error adding member: {result['error']}"


@mcp.tool()
def remove_group_member(group_email: str, member_email: str) -> str:
    """Remove a member from a group.

    Args:
        group_email: The group's email address
        member_email: The email of the user to remove

    Returns:
        Result of removing member
    """
    result = run_gam_command(f"gam update group {group_email} remove member {member_email}")
    if result["success"]:
        return f"Removed {member_email} from {group_email}."
    return f"Error removing member: {result['error']}"


@mcp.tool()
def create_group(email: str, name: str, description: Optional[str] = None) -> str:
    """Create a new group.

    Args:
        email: The new group's email address
        name: Display name for the group
        description: Optional description

    Returns:
        Result of group creation
    """
    cmd = f'gam create group {email} name "{name}"'
    if description:
        cmd += f' description "{description}"'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"Group {email} created successfully."
    return f"Error creating group: {result['error']}"


# =============================================================================
# ORGANIZATIONAL UNIT TOOLS
# =============================================================================

@mcp.tool()
def list_org_units() -> str:
    """List all organizational units in the domain.

    Returns:
        List of organizational units
    """
    result = run_gam_command("gam print orgs")
    if result["success"]:
        return result["output"]
    return f"Error: {result['error']}"


@mcp.tool()
def create_org_unit(path: str, description: Optional[str] = None) -> str:
    """Create a new organizational unit.

    Args:
        path: The OU path (e.g., "/Sales/West Coast")
        description: Optional description

    Returns:
        Result of OU creation
    """
    cmd = f'gam create org "{path}"'
    if description:
        cmd += f' description "{description}"'

    result = run_gam_command(cmd)
    if result["success"]:
        return f"Organizational unit {path} created successfully."
    return f"Error creating OU: {result['error']}"


# =============================================================================
# RAW COMMAND TOOL (for advanced users)
# =============================================================================

@mcp.tool()
def run_gam(command: str) -> str:
    """Execute a raw GAM command (for advanced users).

    Args:
        command: The full GAM command to execute (with or without 'gam' prefix)

    Returns:
        Command output or error message
    """
    result = run_gam_command(command)
    if result["success"]:
        return result["output"] or "Command completed successfully (no output)."
    return f"Error (exit code {result['exit_code']}): {result['error']}"


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
