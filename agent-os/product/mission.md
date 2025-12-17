# Product Mission

## Pitch

u2-mcp is a Python-based MCP server that enables AI assistants to interact with Rocket Universe and UniData databases by exposing MultiValue database capabilities through the Model Context Protocol, preserving native MV semantics rather than flattening to relational models.

## Users

### Primary Customers

- **MultiValue Developers:** Engineers building and maintaining applications on Universe/UniData platforms who want AI-assisted development workflows
- **Database Administrators:** DBAs managing MultiValue databases who need efficient tools for querying, monitoring, and data operations
- **Business Analysts:** Non-technical users requiring ad-hoc data access and reporting from legacy MV systems
- **AI Tool Integrators:** Teams adopting AI-assisted development tools (Claude Code, Cursor, Windsurf) for MV database projects

### User Personas

**Marcus, Senior MV Developer** (35-50)
- **Role:** Lead developer on a Universe-based ERP system
- **Context:** Maintains a 20-year-old codebase with thousands of BASIC programs and complex data relationships
- **Pain Points:** Cannot use modern AI coding assistants for database work; must manually translate between MV concepts and AI-friendly formats; no autocomplete or intelligent query assistance
- **Goals:** Use Claude Code to query data, generate RetrieVe statements, and call BASIC subroutines without leaving the IDE

**Diana, Database Administrator** (40-55)
- **Role:** DBA responsible for multiple Universe instances across business units
- **Context:** Manages critical production databases with strict uptime requirements
- **Pain Points:** Limited tooling compared to SQL databases; repetitive manual tasks for data validation and schema documentation
- **Goals:** Automate routine database operations; generate schema documentation; perform safe ad-hoc queries with AI assistance

**Alex, Business Analyst** (28-40)
- **Role:** Data analyst supporting sales and operations teams
- **Context:** Needs to extract and analyze data from the company's Universe-based order management system
- **Pain Points:** Must request custom reports from IT; cannot self-serve data queries; unfamiliar with RetrieVe syntax
- **Goals:** Ask natural language questions about data and receive formatted results without learning MV query syntax

## The Problem

### The MultiValue AI Gap

The MCP ecosystem provides robust database connectivity for mainstream platforms (PostgreSQL, MySQL, MongoDB, SQLite), enabling AI assistants to query data, generate schemas, and automate database operations. However, **zero MCP servers exist for MultiValue databases** like Rocket Universe, UniData, or D3.

Organizations running mission-critical systems on these platforms face a significant capability gap:
- Cannot leverage AI assistants for database interaction
- No AI-assisted query generation for RetrieVe or UniQuery
- Unable to use modern AI coding tools with their MV databases
- Manual translation required between AI suggestions and MV-native formats

**Impact:** MultiValue shops are locked out of the AI-assisted development revolution, unable to benefit from tools that dramatically improve productivity for teams on conventional databases.

**Our Solution:** A native MCP server using Rocket's official `uopy` package that exposes Universe's full capabilities (file operations, queries, dictionary access, BASIC subroutines, transactions) through MCP tools, preserving MultiValue's unique nested data structures in all outputs.

## Differentiators

### Native MultiValue Semantics

Unlike approaches that flatten MV data to relational tables, u2-mcp preserves the nested, dynamic array structure that makes MultiValue databases powerful. Query results maintain multivalue and subvalue relationships, enabling AI assistants to understand and work with the data as MV developers expect.

This results in accurate AI suggestions that match actual data structures, eliminating the translation layer that causes errors and confusion.

### Official SDK Integration

Built on Rocket's official `uopy` (UniObjects for Python) package rather than ODBC bridges or custom protocols. This ensures compatibility with Universe 11.x, proper connection pooling, and access to native features like BASIC subroutine calls and transaction support.

This results in reliable connectivity, full feature access, and long-term maintainability backed by vendor support.

### AI-Optimized Design

Purpose-built for AI assistant workflows with tools for natural language query validation, contextual syntax help, and structured data export. Safety controls (command blocklist, read-only mode, query timeouts) protect production systems from AI-generated mistakes.

This results in safe, productive AI interactions with mission-critical databases.

## Key Features

### Core Features
- **Connection Management:** Establish, maintain, and gracefully handle Universe database connections with auto-reconnect capability
- **File Operations:** Read, write, and delete records while preserving MultiValue structure; bulk operations for efficiency
- **Query Execution:** Execute RetrieVe queries and TCL commands with timeout protection and result pagination
- **Dictionary Access:** Explore file dictionaries, field definitions, and data structure metadata

### Integration Features
- **BASIC Subroutine Calls:** Invoke cataloged BASIC programs with parameter passing and result capture
- **Transaction Support:** Begin, commit, and rollback transactions for multi-operation consistency
- **Schema Discovery:** Analyze file structures, enumerate accounts, and generate documentation

### AI-Optimized Features
- **Query Validation:** Validate AI-generated queries before execution to catch syntax errors
- **Syntax Resources:** Expose RetrieVe and TCL syntax documentation as MCP resources for AI context
- **Data Export:** Export query results to JSON and CSV formats for downstream analysis
