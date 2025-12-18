"""Connection watchdog for u2-mcp.

Monitors database connection health and automatically recovers from
hung connections that can cause the server to become unresponsive.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from ..config import U2Config

logger = logging.getLogger(__name__)


@dataclass
class WatchdogStats:
    """Statistics tracked by the watchdog."""

    started_at: datetime = field(default_factory=datetime.now)
    checks_total: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    reconnects_forced: int = 0
    consecutive_failures: int = 0
    last_check_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_failure_reason: str | None = None


class ConnectionWatchdog:
    """Monitors connection health and forces reconnection when stuck.

    The watchdog runs periodic health checks on the database connection.
    If checks fail repeatedly (indicating a hung connection), it forces
    a disconnect to allow the next request to reconnect cleanly.

    Args:
        config: U2Config with watchdog settings
        health_check_fn: Function that performs a health check (should be quick)
        force_disconnect_fn: Function to force-disconnect the database
    """

    def __init__(
        self,
        config: "U2Config",
        health_check_fn: Callable[[], bool],
        force_disconnect_fn: Callable[[], None],
    ) -> None:
        self._config = config
        self._health_check_fn = health_check_fn
        self._force_disconnect_fn = force_disconnect_fn
        self._stats = WatchdogStats()
        self._running = False
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    @property
    def stats(self) -> WatchdogStats:
        """Return current watchdog statistics."""
        return self._stats

    @property
    def is_running(self) -> bool:
        """Return whether the watchdog is currently running."""
        return self._running

    def _perform_health_check_sync(self) -> tuple[bool, str | None]:
        """Perform a synchronous health check with timeout.

        Returns:
            Tuple of (success, error_message)
        """
        result: tuple[bool, str | None] = (False, "Timeout")
        check_complete = threading.Event()

        def do_check() -> None:
            nonlocal result
            try:
                success = self._health_check_fn()
                result = (success, None if success else "Health check returned False")
            except Exception as e:
                result = (False, str(e))
            finally:
                check_complete.set()

        # Run health check in a thread with timeout
        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()

        # Wait for completion with timeout
        if check_complete.wait(timeout=self._config.watchdog_timeout):
            return result
        else:
            # Timeout - the thread may still be running but we don't wait
            logger.warning(
                f"Health check timed out after {self._config.watchdog_timeout}s"
            )
            return (False, f"Timeout after {self._config.watchdog_timeout}s")

    async def _run_check(self) -> bool:
        """Run a single health check.

        Returns:
            True if check passed, False otherwise
        """
        self._stats.checks_total += 1
        self._stats.last_check_at = datetime.now()

        # Run the synchronous health check in a thread pool
        loop = asyncio.get_event_loop()
        success, error = await loop.run_in_executor(
            None, self._perform_health_check_sync
        )

        if success:
            self._stats.checks_passed += 1
            self._stats.consecutive_failures = 0
            self._stats.last_success_at = datetime.now()
            logger.debug("Health check passed")
            return True
        else:
            self._stats.checks_failed += 1
            self._stats.consecutive_failures += 1
            self._stats.last_failure_at = datetime.now()
            self._stats.last_failure_reason = error
            logger.warning(
                f"Health check failed ({self._stats.consecutive_failures}/"
                f"{self._config.watchdog_max_failures}): {error}"
            )
            return False

    def _force_reconnect(self) -> None:
        """Force a reconnection by disconnecting the current connection."""
        logger.warning(
            f"Forcing reconnect after {self._stats.consecutive_failures} "
            f"consecutive failures"
        )
        try:
            self._force_disconnect_fn()
            self._stats.reconnects_forced += 1
            self._stats.consecutive_failures = 0
            logger.info("Connection forcefully reset - next request will reconnect")
        except Exception as e:
            logger.error(f"Error during forced disconnect: {e}")

    async def _watchdog_loop(self) -> None:
        """Main watchdog loop that runs periodic health checks."""
        logger.info(
            f"Watchdog started (interval={self._config.watchdog_interval}s, "
            f"timeout={self._config.watchdog_timeout}s, "
            f"max_failures={self._config.watchdog_max_failures})"
        )

        while self._running:
            try:
                # Wait for the interval or stop event
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._config.watchdog_interval,
                    )
                    # Stop event was set
                    break
                except asyncio.TimeoutError:
                    # Normal timeout - time to check
                    pass

                # Perform health check
                passed = await self._run_check()

                # Check if we need to force reconnect
                if (
                    not passed
                    and self._stats.consecutive_failures >= self._config.watchdog_max_failures
                ):
                    self._force_reconnect()

            except Exception as e:
                logger.error(f"Watchdog loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

        logger.info("Watchdog stopped")

    async def start(self) -> None:
        """Start the watchdog background task."""
        if self._running:
            logger.warning("Watchdog already running")
            return

        if not self._config.watchdog_enabled:
            logger.info("Watchdog disabled by configuration")
            return

        self._running = True
        self._stop_event.clear()
        self._stats = WatchdogStats()  # Reset stats
        self._task = asyncio.create_task(self._watchdog_loop())

    async def stop(self) -> None:
        """Stop the watchdog background task."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Watchdog task did not stop cleanly")
                self._task.cancel()
            self._task = None

    def get_status(self) -> dict:
        """Get watchdog status as a dictionary."""
        return {
            "enabled": self._config.watchdog_enabled,
            "running": self._running,
            "interval_seconds": self._config.watchdog_interval,
            "timeout_seconds": self._config.watchdog_timeout,
            "max_failures": self._config.watchdog_max_failures,
            "stats": {
                "started_at": self._stats.started_at.isoformat() if self._stats.started_at else None,
                "checks_total": self._stats.checks_total,
                "checks_passed": self._stats.checks_passed,
                "checks_failed": self._stats.checks_failed,
                "reconnects_forced": self._stats.reconnects_forced,
                "consecutive_failures": self._stats.consecutive_failures,
                "last_check_at": (
                    self._stats.last_check_at.isoformat()
                    if self._stats.last_check_at
                    else None
                ),
                "last_success_at": (
                    self._stats.last_success_at.isoformat()
                    if self._stats.last_success_at
                    else None
                ),
                "last_failure_at": (
                    self._stats.last_failure_at.isoformat()
                    if self._stats.last_failure_at
                    else None
                ),
                "last_failure_reason": self._stats.last_failure_reason,
            },
        }


# Global watchdog instance
_watchdog: ConnectionWatchdog | None = None


def get_watchdog() -> ConnectionWatchdog | None:
    """Get the global watchdog instance."""
    return _watchdog


def init_watchdog(
    config: "U2Config",
    health_check_fn: Callable[[], bool],
    force_disconnect_fn: Callable[[], None],
) -> ConnectionWatchdog:
    """Initialize the global watchdog instance.

    Args:
        config: U2Config with watchdog settings
        health_check_fn: Function to check connection health
        force_disconnect_fn: Function to force disconnect

    Returns:
        The initialized ConnectionWatchdog
    """
    global _watchdog
    _watchdog = ConnectionWatchdog(config, health_check_fn, force_disconnect_fn)
    return _watchdog
