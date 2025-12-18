"""Audit logging for MCP tool calls.

Logs all tool invocations with parameters and results to files for
later analysis and debugging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs MCP tool calls to files for analysis.

    Creates daily log files with JSON-formatted entries for each tool call.
    """

    def __init__(
        self,
        audit_path: str,
        include_results: bool = True,
        max_result_size: int = 10000,
    ):
        """Initialize the audit logger.

        Args:
            audit_path: Directory path for audit log files
            include_results: Whether to include tool results in logs
            max_result_size: Maximum characters to log for results
        """
        self.audit_path = Path(audit_path)
        self.include_results = include_results
        self.max_result_size = max_result_size
        self._current_session_id: str | None = None
        self._session_start: datetime | None = None

        # Ensure audit directory exists
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create audit directory if it doesn't exist."""
        try:
            self.audit_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create audit directory {self.audit_path}: {e}")

    def _get_log_file_path(self) -> Path:
        """Get the log file path for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.audit_path / f"audit-{today}.jsonl"

    def start_session(self, session_id: str | None = None) -> str:
        """Start a new audit session.

        Args:
            session_id: Optional session identifier

        Returns:
            The session ID being used
        """
        self._session_start = datetime.now()
        self._current_session_id = session_id or self._session_start.strftime("%Y%m%d-%H%M%S-%f")

        self._write_entry(
            {
                "event": "session_start",
                "session_id": self._current_session_id,
                "timestamp": self._session_start.isoformat(),
            }
        )

        return self._current_session_id

    def end_session(self) -> None:
        """End the current audit session."""
        if self._current_session_id:
            self._write_entry(
                {
                    "event": "session_end",
                    "session_id": self._current_session_id,
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": (
                        (datetime.now() - self._session_start).total_seconds()
                        if self._session_start
                        else None
                    ),
                }
            )
        self._current_session_id = None
        self._session_start = None

    def log_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Log a tool invocation.

        Args:
            tool_name: Name of the tool being called
            parameters: Parameters passed to the tool
            result: Result returned by the tool (optional)
            error: Error message if tool failed (optional)
            duration_ms: Execution time in milliseconds (optional)
        """
        entry: dict[str, Any] = {
            "event": "tool_call",
            "timestamp": datetime.now().isoformat(),
            "session_id": self._current_session_id,
            "tool": tool_name,
            "parameters": self._sanitize_parameters(parameters),
        }

        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        if error:
            entry["error"] = error
            entry["status"] = "error"
        else:
            entry["status"] = "success"

        if self.include_results and result is not None:
            entry["result"] = self._truncate_result(result)

        self._write_entry(entry)

    def log_query(
        self,
        query: str,
        result_count: int | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Log a database query execution.

        Args:
            query: The query that was executed
            result_count: Number of results returned (optional)
            error: Error message if query failed (optional)
            duration_ms: Execution time in milliseconds (optional)
        """
        entry: dict[str, Any] = {
            "event": "query",
            "timestamp": datetime.now().isoformat(),
            "session_id": self._current_session_id,
            "query": query,
        }

        if result_count is not None:
            entry["result_count"] = result_count

        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        if error:
            entry["error"] = error
            entry["status"] = "error"
        else:
            entry["status"] = "success"

        self._write_entry(entry)

    def log_error(
        self, error_type: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Log an error event.

        Args:
            error_type: Type/category of error
            message: Error message
            details: Additional error details (optional)
        """
        entry: dict[str, Any] = {
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "session_id": self._current_session_id,
            "error_type": error_type,
            "message": message,
        }

        if details:
            entry["details"] = details

        self._write_entry(entry)

    def _sanitize_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters to avoid logging sensitive data.

        Args:
            params: Raw parameters

        Returns:
            Sanitized parameters with sensitive values masked
        """
        sensitive_keys = {"password", "secret", "token", "key", "credential"}
        sanitized: dict[str, Any] = {}

        for key, value in params.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            else:
                sanitized[key] = value

        return sanitized

    def _truncate_result(self, result: Any) -> Any:
        """Truncate large results to avoid huge log files.

        Args:
            result: The result to potentially truncate

        Returns:
            Truncated result if necessary
        """
        try:
            result_str = json.dumps(result, default=str)
            if len(result_str) > self.max_result_size:
                return {
                    "_truncated": True,
                    "_original_size": len(result_str),
                    "_preview": result_str[: self.max_result_size] + "...",
                }
            return result
        except (TypeError, ValueError):
            return {"_type": str(type(result)), "_str": str(result)[:1000]}

    def _write_entry(self, entry: dict[str, Any]) -> None:
        """Write an entry to the audit log file.

        Args:
            entry: The log entry to write
        """
        try:
            log_file = self._get_log_file_path()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {e}")


# Global audit logger instance (initialized by server)
_audit_logger: AuditLogger | None = None


def init_audit_logger(
    audit_path: str,
    include_results: bool = True,
    max_result_size: int = 10000,
) -> AuditLogger:
    """Initialize the global audit logger.

    Args:
        audit_path: Directory path for audit log files
        include_results: Whether to include tool results in logs
        max_result_size: Maximum characters to log for results

    Returns:
        The initialized AuditLogger instance
    """
    global _audit_logger
    _audit_logger = AuditLogger(
        audit_path=audit_path,
        include_results=include_results,
        max_result_size=max_result_size,
    )
    return _audit_logger


def get_audit_logger() -> AuditLogger | None:
    """Get the global audit logger instance.

    Returns:
        The AuditLogger instance, or None if not initialized
    """
    return _audit_logger


def audit_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    result: Any | None = None,
    error: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """Convenience function to log a tool call if auditing is enabled.

    Args:
        tool_name: Name of the tool being called
        parameters: Parameters passed to the tool
        result: Result returned by the tool (optional)
        error: Error message if tool failed (optional)
        duration_ms: Execution time in milliseconds (optional)
    """
    if _audit_logger:
        _audit_logger.log_tool_call(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            error=error,
            duration_ms=duration_ms,
        )
