"""Transaction management tools for u2-mcp."""

import logging
from typing import Any

from ..server import get_connection_manager, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
def begin_transaction() -> dict[str, Any]:
    """Begin a database transaction.

    Starts a new transaction. All subsequent write operations (write_record,
    delete_record) will be part of this transaction until commit_transaction
    or rollback_transaction is called.

    Returns:
        Dictionary containing:
        - status: success or error
        - in_transaction: True if transaction is now active
        - started_at: Timestamp when transaction started

    Note:
        Only one transaction can be active at a time.
        Attempting to start a new transaction while one is active will fail.
    """
    manager = get_connection_manager()

    if manager.config.read_only:
        return {
            "error": "Transactions not available in read-only mode",
            "in_transaction": False,
        }

    if manager.in_transaction:
        return {
            "error": "Transaction already in progress",
            "in_transaction": True,
        }

    try:
        manager.begin_transaction()
        return {
            "status": "success",
            "message": "Transaction started",
            "in_transaction": True,
            "started_at": manager._transaction.started_at.isoformat()
            if manager._transaction.started_at
            else None,
        }
    except Exception as e:
        logger.error(f"Error starting transaction: {e}")
        return {"error": str(e), "in_transaction": manager.in_transaction}


@mcp.tool()
def commit_transaction() -> dict[str, Any]:
    """Commit the current transaction.

    Saves all changes made since begin_transaction was called.
    The transaction is closed after commit.

    Returns:
        Dictionary containing:
        - status: success or error
        - in_transaction: False after successful commit
        - message: Confirmation message

    Note:
        If no transaction is active, returns an error.
    """
    manager = get_connection_manager()

    if not manager.in_transaction:
        return {
            "error": "No transaction in progress",
            "in_transaction": False,
        }

    try:
        manager.commit_transaction()
        return {
            "status": "success",
            "message": "Transaction committed successfully",
            "in_transaction": False,
        }
    except Exception as e:
        logger.error(f"Error committing transaction: {e}")
        return {
            "error": str(e),
            "in_transaction": manager.in_transaction,
            "message": "Transaction may still be active",
        }


@mcp.tool()
def rollback_transaction() -> dict[str, Any]:
    """Rollback the current transaction.

    Discards all changes made since begin_transaction was called.
    The transaction is closed after rollback.

    Returns:
        Dictionary containing:
        - status: success or error
        - in_transaction: False after successful rollback
        - message: Confirmation message

    Note:
        If no transaction is active, returns an error.
    """
    manager = get_connection_manager()

    if not manager.in_transaction:
        return {
            "error": "No transaction in progress",
            "in_transaction": False,
        }

    try:
        manager.rollback_transaction()
        return {
            "status": "success",
            "message": "Transaction rolled back successfully",
            "in_transaction": False,
        }
    except Exception as e:
        logger.error(f"Error rolling back transaction: {e}")
        return {
            "error": str(e),
            "in_transaction": manager.in_transaction,
            "message": "Transaction may still be active",
        }


@mcp.tool()
def get_transaction_status() -> dict[str, Any]:
    """Get the current transaction status.

    Returns information about whether a transaction is active
    and when it was started.

    Returns:
        Dictionary containing:
        - in_transaction: True if transaction is active
        - started_at: Timestamp when transaction started (if active)
        - read_only_mode: Whether server is in read-only mode
    """
    manager = get_connection_manager()

    return {
        "in_transaction": manager.in_transaction,
        "started_at": manager._transaction.started_at.isoformat()
        if manager._transaction.started_at
        else None,
        "read_only_mode": manager.config.read_only,
    }
