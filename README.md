# GAM MCP Server

An MCP (Model Context Protocol) server that provides Google Workspace administration tools via GAM7 commands. Use this with Claude Code to manage your Google Workspace domains using natural language.

## Prerequisites

- Python 3.11+
- [GAM7](https://github.com/taers232c/GAMADV-XTD3) installed and configured
- Claude Code (or another MCP client)

## Installation

```bash
# Clone the repository
git clone https://github.com/limehawk/gam-multi.git
cd gam-multi

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Configuration for Claude Code

Add this to your Claude Code MCP settings (`~/.claude.json` or via the CLI):

```json
{
  "mcpServers": {
    "gam": {
      "command": "uv",
      "args": ["--directory", "/path/to/gam-multi", "run", "gam-mcp"]
    }
  }
}
```

Or if installed globally:

```json
{
  "mcpServers": {
    "gam": {
      "command": "gam-mcp"
    }
  }
}
```

## Available Tools

### User Management
- `list_users` - List users with optional filtering
- `get_user_info` - Get detailed user information
- `create_user` - Create a new user
- `suspend_user` - Suspend a user account
- `unsuspend_user` - Reactivate a suspended user
- `reset_password` - Reset user password
- `move_user_to_ou` - Move user to organizational unit

### Security
- `sign_out_user` - Sign out all sessions (destructive)
- `revoke_tokens` - Revoke OAuth tokens (destructive)

### Group Management
- `list_groups` - List all groups
- `get_group_info` - Get group details
- `list_group_members` - List group members
- `add_group_member` - Add member to group
- `remove_group_member` - Remove member from group
- `create_group` - Create a new group

### Organizational Units
- `list_org_units` - List all OUs
- `create_org_unit` - Create a new OU

### Advanced
- `run_gam` - Execute any GAM command directly

## Usage Examples

Once configured, just ask Claude:

- "List all suspended users"
- "Create a new user john.doe@example.com"
- "Reset the password for jane@example.com"
- "Add bob@example.com to the sales-team group"
- "Show me users who haven't logged in for 90 days"

## GAM Configuration

This MCP server uses your existing GAM configuration. Make sure GAM is properly set up:

```bash
# Verify GAM is working
gam info domain

# Check your configured domains
gam print users maxresults 1
```

## License

MIT
