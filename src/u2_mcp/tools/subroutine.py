"""BASIC subroutine integration tools for u2-mcp."""

import logging
from typing import Any

import uopy

from ..server import get_connection_manager, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
def call_subroutine(
    name: str,
    args: list[str] | None = None,
    num_args: int | None = None,
) -> dict[str, Any]:
    """Call a cataloged BASIC subroutine with arguments.

    Executes a cataloged BASIC program and returns the results.
    Arguments are passed by reference, so output arguments will
    be returned in the response.

    Args:
        name: Name of the cataloged subroutine
        args: List of argument values to pass (input arguments).
              Arguments are passed as strings and converted by the subroutine.
        num_args: Total number of arguments the subroutine expects.
                  If not specified, uses len(args). Required if subroutine
                  has output-only arguments.

    Returns:
        Dictionary containing:
        - status: success or error
        - args_out: List of argument values after subroutine execution
        - original_args: The input arguments that were passed

    Example:
        # Call GET.CUSTOMER.DATA with customer ID, returns data in args 2-3
        call_subroutine("GET.CUSTOMER.DATA", ["CUST001", "", ""], num_args=3)
    """
    manager = get_connection_manager()

    args = args or []
    actual_num_args = num_args if num_args is not None else len(args)

    if actual_num_args < len(args):
        return {
            "error": f"num_args ({actual_num_args}) cannot be less than args length ({len(args)})",
            "subroutine": name,
        }

    try:
        session = manager.get_session()

        # Create subroutine object with specified number of arguments
        sub = uopy.Subroutine(name, actual_num_args, session=session)

        # Set input arguments
        for i, arg in enumerate(args):
            sub.set_arg(i, str(arg) if arg is not None else "")

        # Initialize remaining args as empty strings
        for i in range(len(args), actual_num_args):
            sub.set_arg(i, "")

        # Call the subroutine
        sub.call()

        # Collect output arguments
        args_out = [sub.get_arg(i) for i in range(actual_num_args)]

        return {
            "status": "success",
            "subroutine": name,
            "args_in": args,
            "args_out": args_out,
            "num_args": actual_num_args,
        }

    except Exception as e:
        logger.error(f"Error calling subroutine {name}: {e}")
        return {"error": str(e), "subroutine": name}


@mcp.tool()
def list_catalog(pattern: str = "*") -> dict[str, Any]:
    """List available cataloged programs in the account.

    Searches the system catalog for programs matching the pattern.
    This includes BASIC subroutines that can be called with call_subroutine.

    Args:
        pattern: Program name pattern (supports * wildcard).
                 Default "*" lists all cataloged programs.

    Returns:
        Dictionary containing list of program names and count.
    """
    manager = get_connection_manager()

    try:
        # Use CATALOG command to list programs
        # Different Universe versions may have different syntax
        if pattern == "*":
            output = manager.execute_command("CATALOG")
        else:
            # Convert wildcard to LIKE pattern
            like_pattern = pattern.replace("*", "...")
            output = manager.execute_command(f'CATALOG "{like_pattern}"')

        # Parse catalog output to extract program names
        programs = _parse_catalog_output(output)

        # If CATALOG command doesn't work well, try alternative
        if not programs:
            # Try SELECT from VOC for cataloged items
            manager.execute_command('SELECT VOC WITH F1 = "V" AND WITH F2 LIKE "...CATALOG..."')

            # Or try the catalog pointer file
            try:
                manager.execute_command("SELECT &SYSCAT&")
                select = manager.create_select_list()
                while True:
                    prog_name = select.next()
                    if prog_name is None or str(prog_name) == "":
                        break
                    if pattern == "*" or _matches_pattern(str(prog_name), pattern):
                        programs.append(str(prog_name))
            except Exception:
                pass

        return {
            "pattern": pattern,
            "programs": programs,
            "count": len(programs),
            "raw_output": output,
        }

    except Exception as e:
        logger.error(f"Error listing catalog: {e}")
        return {"error": str(e), "pattern": pattern}


def _parse_catalog_output(output: str) -> list[str]:
    """Parse CATALOG command output to extract program names.

    Args:
        output: Raw CATALOG command output

    Returns:
        List of program names
    """
    programs: list[str] = []
    lines = output.strip().split("\n")

    for line in lines:
        line = line.strip()
        # Skip empty lines, headers, and decorations
        if not line:
            continue
        if line.startswith("*") or line.startswith("-") or line.startswith("="):
            continue
        if any(
            header in line.upper()
            for header in ["CATALOG", "PROGRAM", "NAME", "LOCAL", "GLOBAL", "DIRECT"]
        ):
            continue

        # Try to extract program name (usually first column)
        parts = line.split()
        if parts:
            prog_name = parts[0]
            # Skip if it looks like a count or status
            if not prog_name.isdigit() and prog_name not in ("LOCAL", "GLOBAL", "DIRECT"):
                programs.append(prog_name)

    return programs


def _matches_pattern(name: str, pattern: str) -> bool:
    """Check if name matches simple wildcard pattern.

    Args:
        name: String to check
        pattern: Pattern with * wildcards

    Returns:
        True if name matches pattern
    """
    import fnmatch

    return fnmatch.fnmatch(name.upper(), pattern.upper().replace("...", "*"))
