# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in u2-mcp, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly with details of the vulnerability
3. Include steps to reproduce the issue
4. Allow reasonable time for a fix before public disclosure

## Security Features

### Credential Protection

- Database credentials are loaded from environment variables, never hardcoded
- Credentials are never logged or exposed in error messages
- The `U2_PASSWORD` field is treated as sensitive data

### Command Blocking

Dangerous TCL commands are blocked by default:

- `DELETE.FILE` - Prevents file deletion
- `CLEAR.FILE` - Prevents data clearing
- `CNAME` - Prevents file renaming
- `CREATE.FILE` - Prevents file creation (in read-only mode)

Configure additional blocked commands via `U2_BLOCKED_COMMANDS`:

```bash
export U2_BLOCKED_COMMANDS="DELETE.FILE,CLEAR.FILE,CNAME,ED,AE"
```

### Read-Only Mode

Enable read-only mode to prevent all write operations:

```bash
export U2_READ_ONLY=true
```

This disables:
- `write_record`
- `delete_record`
- `begin_transaction` / `commit_transaction`
- Any TCL command that modifies data

### Query Validation

The `execute_query` tool only allows safe query commands:
- `LIST`
- `SELECT`
- `SSELECT`
- `SORT`
- `COUNT`
- `SUM`

Commands like `DELETE`, `COPY`, `ED` are rejected.

### Result Limiting

Query results are limited by `U2_MAX_RECORDS` (default: 10,000) to prevent accidental large data exports.

### CORS Configuration (HTTP Mode)

When running in HTTP mode, configure CORS origins to restrict access:

```bash
export U2_HTTP_CORS_ORIGINS="https://trusted-app.example.com"
```

## Best Practices

1. **Use read-only mode** for exploration and development
2. **Restrict blocked commands** based on your security requirements
3. **Use dedicated service accounts** with minimal Universe permissions
4. **Store credentials securely** using secrets management (not plain text)
5. **Limit network access** to the HTTP server if deployed centrally
6. **Review knowledge files** - they may contain sensitive schema information

## Known Limitations

- The MCP protocol transmits data in plain text over stdio
- HTTP mode should use HTTPS in production (configure via reverse proxy)
- Knowledge files are stored as plain text markdown
