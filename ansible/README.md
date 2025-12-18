# Ansible Deployment for u2-mcp

Deploy the u2-mcp server to remote Linux servers using Ansible.

## Prerequisites

- Ansible 2.9+ installed on your control machine
- SSH access to target servers
- Target servers running Debian/Ubuntu or RHEL/CentOS/Rocky

## Quick Start

1. **Edit inventory**

   ```bash
   cp inventory/hosts.yml inventory/production.yml
   # Edit with your server details
   ```

2. **Set up vault for secrets** (recommended)

   ```bash
   # Create encrypted vars file
   ansible-vault create inventory/group_vars/mcp_servers/vault.yml
   ```

   Add to vault:
   ```yaml
   vault_u2_password: "your-secure-password"
   ```

3. **Run deployment**

   ```bash
   # With vault
   ansible-playbook -i inventory/production.yml deploy.yml --ask-vault-pass

   # Or with password prompt
   ansible-playbook -i inventory/production.yml deploy.yml
   ```

## Configuration Variables

### Required Variables

| Variable | Description |
|----------|-------------|
| `u2_host` | Universe/UniData server hostname |
| `u2_user` | Database username |
| `u2_password` | Database password |
| `u2_account` | Account name |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `u2_mcp_version` | `latest` | Package version to install |
| `u2_service` | `uvcs` | `uvcs` (Universe) or `udcs` (UniData) |
| `u2_port` | `31438` | Database port |
| `u2_ssl` | `false` | Enable SSL |
| `u2_read_only` | `false` | Read-only mode |
| `u2_max_records` | `10000` | Max records per query |
| `u2_mcp_transport` | `stdio` | Transport: `stdio`, `sse`, `streamable-http` |
| `u2_mcp_http_host` | `127.0.0.1` | HTTP bind address (for sse/http) |
| `u2_mcp_http_port` | `8080` | HTTP port (for sse/http) |

## Example Inventory

```yaml
all:
  children:
    mcp_servers:
      hosts:
        prod-mcp:
          ansible_host: 10.0.1.50
          ansible_user: deploy
          u2_host: "universe-prod.internal"
          u2_account: "PRODUCTION"
          u2_read_only: true
```

## Managing the Service

After deployment, on the target server:

```bash
# Check status
sudo systemctl status u2-mcp

# View logs
sudo journalctl -u u2-mcp -f

# Restart
sudo systemctl restart u2-mcp
```

## Directory Structure

```
/opt/u2-mcp/           # Installation directory
  venv/                # Python virtual environment
/etc/u2-mcp/           # Configuration
  .env                 # Environment variables
```

## Testing Locally

To test with a local VM or container:

```bash
# Use localhost inventory
ansible-playbook -i "localhost," -c local deploy.yml \
  -e "u2_host=myserver" \
  -e "u2_user=admin" \
  -e "u2_password=secret" \
  -e "u2_account=TEST"
```
