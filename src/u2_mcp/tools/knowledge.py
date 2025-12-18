"""Knowledge persistence tools for u2-mcp.

These tools allow Claude to save and retrieve learned information
about the Universe database across sessions.
"""

import logging
from typing import Any

from ..server import mcp
from ..utils.knowledge import get_knowledge_store

logger = logging.getLogger(__name__)


@mcp.tool()
def save_knowledge(topic: str, content: str, append: bool = False) -> dict[str, Any]:
    """Save learned information about the Universe database.

    Use this to persist useful discoveries about the database schema,
    file structures, query patterns, and data meanings. This information
    will be available in future conversations.

    Good things to save:
    - File purposes (e.g., "AR-CUST contains customer master records")
    - Field meanings (e.g., "In CUSTOMERS, field 1 is name, field 5 is phone")
    - Working query patterns that produced good results
    - Relationships between files
    - Data format notes (date formats, codes, etc.)

    Args:
        topic: A short descriptive name for this knowledge
               (e.g., "CUSTOMERS file", "Invoice queries", "Date formats")
        content: The knowledge to save. Use markdown formatting.
        append: If True, add to existing topic. If False, replace it.

    Returns:
        Status of the save operation.

    Examples:
        save_knowledge("AR-CUST file", "Customer master file. Key is customer number.")
        save_knowledge("Date formats", "Dates stored as internal format. Use D2/ conversion.")
    """
    try:
        store = get_knowledge_store()
        result = store.save_topic(topic, content, append=append)
        logger.info(f"Saved knowledge topic: {topic}")
        return result
    except Exception as e:
        logger.error(f"Error saving knowledge: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def list_knowledge() -> dict[str, Any]:
    """List all saved knowledge topics.

    Returns a list of topics that have been saved about this database.
    Use get_knowledge_topic to retrieve the full content of a specific topic,
    or get_all_knowledge to retrieve everything at once.

    Returns:
        Dictionary containing list of topics with summaries.
    """
    try:
        store = get_knowledge_store()
        topics = store.list_topics()
        return {
            "topics": topics,
            "count": len(topics),
            "knowledge_file": str(store.path),
        }
    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_all_knowledge() -> dict[str, Any]:
    """Get ALL saved knowledge about this Universe database.

    IMPORTANT: Call this tool at the start of conversations to retrieve
    previously learned information about the database. This includes:
    - File descriptions and purposes
    - Field definitions and meanings
    - Working query patterns
    - Relationships between files
    - Data format notes and conventions

    This knowledge was saved from previous conversations to help you
    work more efficiently with this specific database.

    Returns:
        All saved knowledge as markdown text.
    """
    try:
        store = get_knowledge_store()
        content = store.get_all()
        topics = store.list_topics()
        return {
            "status": "success",
            "knowledge": content,
            "topic_count": len(topics),
            "topics": [t["topic"] for t in topics],
        }
    except Exception as e:
        logger.error(f"Error getting all knowledge: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_knowledge_topic(topic: str) -> dict[str, Any]:
    """Get saved knowledge for a specific topic.

    Retrieves the full content of a previously saved knowledge topic.

    Args:
        topic: The topic name to retrieve.

    Returns:
        The topic content or error if not found.
    """
    try:
        store = get_knowledge_store()
        content = store.get_topic(topic)
        if content is None:
            return {
                "status": "not_found",
                "error": f"Topic '{topic}' not found",
                "available_topics": [t["topic"] for t in store.list_topics()],
            }
        return {
            "status": "found",
            "topic": topic,
            "content": content,
        }
    except Exception as e:
        logger.error(f"Error getting knowledge topic: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def search_knowledge(query: str) -> dict[str, Any]:
    """Search saved knowledge for specific information.

    Searches all saved knowledge for mentions of the query string.
    Useful for finding previously learned information about specific
    files, fields, or concepts.

    Args:
        query: Text to search for (case-insensitive).

    Returns:
        List of matching topics and relevant lines.
    """
    try:
        store = get_knowledge_store()
        results = store.search(query)
        return {
            "query": query,
            "results": results,
            "match_count": len(results),
        }
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def delete_knowledge(topic: str, confirm: bool = False) -> dict[str, Any]:
    """Delete a saved knowledge topic.

    Removes a topic from the knowledge base. Requires confirmation.

    Args:
        topic: The topic name to delete.
        confirm: Must be True to execute the deletion.

    Returns:
        Status of the delete operation.
    """
    if not confirm:
        return {
            "status": "confirmation_required",
            "message": f"Set confirm=True to delete topic '{topic}'",
            "topic": topic,
        }

    try:
        store = get_knowledge_store()
        result = store.delete_topic(topic)
        logger.info(f"Deleted knowledge topic: {topic}")
        return result
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        return {"status": "error", "error": str(e)}
