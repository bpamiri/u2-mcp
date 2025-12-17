# Product Roadmap

## Phase 1: Core Connectivity (MVP)

1. [ ] Connection Management — Implement connect, disconnect, and list_connections tools with configuration via environment variables, auto-reconnect on failure, and connection state tracking `M`

2. [ ] File Information Tools — Create get_file_info and list_files tools to enumerate available files and retrieve file metadata (type, modulo, separation, record count) `S`

3. [ ] Single Record Operations — Implement read_record, write_record, and delete_record tools with proper MultiValue array handling, preserving value marks and subvalue marks in JSON output `M`

4. [ ] Bulk Record Operations — Add read_records tool for efficient multi-record retrieval with configurable batch sizes and pagination support `S`

5. [ ] Query Execution Tools — Create execute_query tool for RetrieVe/UniQuery with timeout protection, result pagination, and structured JSON output preserving MV semantics `M`

6. [ ] TCL Command Execution — Implement execute_tcl tool for general TCL commands with output capture, safety blocklist for dangerous commands, and optional read-only mode `M`

7. [ ] Select List Management — Add get_select_list tool to retrieve and work with active select lists from query operations `S`

8. [ ] Dictionary Listing — Create list_dictionary tool to enumerate all dictionary items (D-type and I-type) for a given file `S`

9. [ ] Field Definition Access — Implement get_field_definition tool to retrieve detailed field metadata including conversion codes, correlatives, and display formatting `S`

10. [ ] File Description Tool — Add describe_file tool that combines dictionary and file info into a comprehensive schema description suitable for AI context `M`

## Phase 2: Advanced Features

11. [ ] BASIC Subroutine Invocation — Implement call_subroutine tool to execute cataloged BASIC programs with typed parameter passing and return value capture `L`

12. [ ] Catalog Discovery — Create list_catalog tool to enumerate available cataloged subroutines with signature information where available `M`

13. [ ] Transaction Begin — Implement begin_transaction tool to start a database transaction with configurable isolation level `S`

14. [ ] Transaction Commit — Add commit_transaction tool to commit pending changes within an active transaction `XS`

15. [ ] Transaction Rollback — Add rollback_transaction tool to abort and roll back an active transaction `XS`

16. [ ] File Structure Analysis — Create analyze_file_structure tool that samples records to infer field usage patterns, data types, and common value distributions `L`

17. [ ] Account Information — Implement get_account_info tool to retrieve account-level metadata, VOC entries, and configuration details `M`

## Phase 3: AI-Optimized Features

18. [ ] Query Syntax Resource — Create MCP resource exposing RetrieVe/UniQuery syntax documentation, operators, and keywords for AI assistant context `M`

19. [ ] Query Examples Resource — Add MCP resource with curated example queries demonstrating common patterns and MV-specific constructs `S`

20. [ ] Query Validation Tool — Implement validate_query tool that parses and validates query syntax before execution, returning specific error messages for AI correction `M`

21. [ ] JSON Export — Create export_to_json tool for exporting query results or file contents to structured JSON with configurable flattening options `S`

22. [ ] CSV Export — Add export_to_csv tool with configurable delimiters and multivalue handling strategies (expand rows, concatenate, first-value-only) `S`

23. [ ] Error Context Enhancement — Improve all error responses with actionable suggestions, related documentation links, and example corrections for AI learning `M`

---

> Notes
> - Phase 1 delivers a complete, usable MCP server for basic Universe database interaction
> - Each tool includes comprehensive input validation, timeout handling, and structured error responses
> - All output formats preserve MultiValue semantics unless explicit flattening is requested
> - Safety controls (blocklist, read-only mode, timeouts) are configurable per-connection
> - Phase 2 unlocks integration with existing BASIC codebases and transactional workflows
> - Phase 3 optimizes the AI assistant experience with validation, documentation, and export capabilities
