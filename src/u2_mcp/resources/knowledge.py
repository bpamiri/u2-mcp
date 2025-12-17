"""Knowledge resource for u2-mcp.

Exposes saved database knowledge to Claude at the start of conversations.
"""

from ..server import mcp
from ..utils.knowledge import get_knowledge_store


@mcp.resource("u2://knowledge")
def get_database_knowledge() -> str:
    """Previously learned information about this Universe database.

    This resource contains all saved knowledge about the database including:
    - File descriptions and purposes
    - Field definitions and meanings
    - Working query patterns
    - Data format notes
    - Relationships between files

    This knowledge was saved from previous conversations to help
    Claude work more efficiently with this database.
    """
    store = get_knowledge_store()
    return store.get_all()
