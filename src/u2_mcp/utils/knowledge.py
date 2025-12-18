"""Knowledge persistence utility for u2-mcp.

Stores learned information about the Universe database to speed up
future interactions. Knowledge is stored as a markdown file that
Claude can read and update.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Default knowledge file location
DEFAULT_KNOWLEDGE_PATH = Path.home() / ".u2-mcp" / "knowledge.md"


class KnowledgeStore:
    """Manages persistent knowledge about the Universe database."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Initialize the knowledge store.

        Args:
            path: Path to the knowledge file. Defaults to ~/.u2-mcp/knowledge.md
        """
        self.path = Path(path) if path else DEFAULT_KNOWLEDGE_PATH
        self._ensure_directory()

    def _normalize_topic(self, topic: str) -> str:
        """Normalize a topic name for consistent matching.

        Removes leading ## prefix, strips whitespace, and normalizes case.
        """
        # Remove leading ## if present
        topic = re.sub(r"^#+\s*", "", topic.strip())
        return topic.strip()

    def _find_similar_topic(self, topic: str) -> str | None:
        """Find an existing topic that matches or is similar to the given topic.

        Uses normalized matching to find topics like:
        - "CUST-MAST file" matches "CUST-MAST - Customer Master"
        - "INV-MAST" matches "INV-MAST - Inventory Master"

        Returns the existing topic name if found, None otherwise.
        """
        normalized = self._normalize_topic(topic).lower()
        existing_topics = [t["topic"] for t in self.list_topics()]

        # First try exact match (case-insensitive)
        for existing in existing_topics:
            if existing.lower() == normalized:
                return existing

        # Extract the file name pattern (e.g., "CUST-MAST" from "CUST-MAST file")
        # Match patterns like "WORD-WORD" at the start
        file_pattern = re.match(r"^([A-Z][\w-]+)", normalized, re.IGNORECASE)
        if file_pattern:
            file_name = file_pattern.group(1).lower()
            for existing in existing_topics:
                existing_lower = existing.lower()
                # Check if the file name is at the start of an existing topic
                if existing_lower.startswith(file_name):
                    return existing

        return None

    def _ensure_directory(self) -> None:
        """Create the knowledge directory if it doesn't exist."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> str:
        """Read the knowledge file contents."""
        if self.path.exists():
            return self.path.read_text(encoding="utf-8")
        return ""

    def _write_file(self, content: str) -> None:
        """Write content to the knowledge file."""
        self.path.write_text(content, encoding="utf-8")

    def get_all(self) -> str:
        """Get all stored knowledge as markdown.

        Returns:
            The full knowledge file contents, or a default message if empty.
        """
        content = self._read_file()
        if not content.strip():
            return "# U2 Database Knowledge\n\nNo knowledge has been saved yet.\n"
        return content

    def list_topics(self) -> list[dict[str, str]]:
        """List all knowledge topics.

        Returns:
            List of dicts with 'topic' and 'summary' keys.
        """
        content = self._read_file()
        if not content:
            return []

        topics = []
        # Parse markdown headers (## Topic Name)
        pattern = r"^## (.+)$"
        lines = content.split("\n")

        current_topic = None
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                current_topic = match.group(1).strip()
                # Get first non-empty line after header as summary
                summary = ""
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip() and not lines[j].startswith("#"):
                        summary = lines[j].strip()[:100]
                        if len(lines[j].strip()) > 100:
                            summary += "..."
                        break
                topics.append({"topic": current_topic, "summary": summary})

        return topics

    def get_topic(self, topic: str) -> str | None:
        """Get knowledge for a specific topic.

        Args:
            topic: The topic name to retrieve.

        Returns:
            The topic content, or None if not found.
        """
        content = self._read_file()
        if not content:
            return None

        # Normalize and find similar topic
        topic = self._normalize_topic(topic)
        similar_topic = self._find_similar_topic(topic)
        if similar_topic:
            topic = similar_topic

        # Find the topic section
        pattern = rf"^## {re.escape(topic)}$"
        lines = content.split("\n")

        start_idx = None
        for i, line in enumerate(lines):
            if re.match(pattern, line, re.IGNORECASE):
                start_idx = i
                break

        if start_idx is None:
            return None

        # Find the end of this section (next ## header or end of file)
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            if re.match(r"^## ", lines[i]):
                end_idx = i
                break

        return "\n".join(lines[start_idx:end_idx]).strip()

    def save_topic(self, topic: str, content: str, append: bool = False) -> dict[str, Any]:
        """Save knowledge for a topic.

        Args:
            topic: The topic name (will become a ## header).
            content: The knowledge content to save.
            append: If True, append to existing topic. If False, replace.

        Returns:
            Status dict with success/error info.
        """
        existing = self._read_file()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Normalize the topic name
        topic = self._normalize_topic(topic)

        # Check if a similar topic already exists
        similar_topic = self._find_similar_topic(topic)
        if similar_topic:
            # Use the existing topic name for consistency
            topic = similar_topic

        # Check if topic exists
        pattern = rf"^## {re.escape(topic)}$"
        lines = existing.split("\n") if existing else []

        topic_idx = None
        for i, line in enumerate(lines):
            if re.match(pattern, line, re.IGNORECASE):
                topic_idx = i
                break

        # Format the new content
        formatted_content = f"## {topic}\n\n*Updated: {timestamp}*\n\n{content.strip()}\n"

        if topic_idx is not None:
            # Topic exists - find its end
            end_idx = len(lines)
            for i in range(topic_idx + 1, len(lines)):
                if re.match(r"^## ", lines[i]):
                    end_idx = i
                    break

            if append:
                # Append to existing content
                existing_content = "\n".join(lines[topic_idx:end_idx])
                formatted_content = (
                    f"{existing_content}\n\n### Addition ({timestamp})\n\n{content.strip()}\n"
                )

            # Replace the section
            new_lines = lines[:topic_idx] + formatted_content.split("\n") + lines[end_idx:]
            new_content = "\n".join(new_lines)
        else:
            # New topic - add header if file is empty
            if not existing.strip():
                new_content = f"# U2 Database Knowledge\n\n{formatted_content}"
            else:
                new_content = f"{existing.rstrip()}\n\n{formatted_content}"

        self._write_file(new_content)

        return {
            "status": "saved",
            "topic": topic,
            "action": "appended" if append and topic_idx is not None else "saved",
            "timestamp": timestamp,
        }

    def delete_topic(self, topic: str) -> dict[str, Any]:
        """Delete a knowledge topic.

        Args:
            topic: The topic name to delete.

        Returns:
            Status dict with success/error info.
        """
        content = self._read_file()
        if not content:
            return {"status": "error", "error": "No knowledge file exists"}

        # Normalize and find similar topic
        original_topic = topic
        topic = self._normalize_topic(topic)
        similar_topic = self._find_similar_topic(topic)
        if similar_topic:
            topic = similar_topic

        pattern = rf"^## {re.escape(topic)}$"
        lines = content.split("\n")

        topic_idx = None
        for i, line in enumerate(lines):
            if re.match(pattern, line, re.IGNORECASE):
                topic_idx = i
                break

        if topic_idx is None:
            return {"status": "error", "error": f"Topic '{original_topic}' not found"}

        # Find end of section
        end_idx = len(lines)
        for i in range(topic_idx + 1, len(lines)):
            if re.match(r"^## ", lines[i]):
                end_idx = i
                break

        # Remove the section
        new_lines = lines[:topic_idx] + lines[end_idx:]
        # Clean up extra blank lines
        new_content = re.sub(r"\n{3,}", "\n\n", "\n".join(new_lines))

        self._write_file(new_content)

        return {"status": "deleted", "topic": topic}

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search knowledge for a query string.

        Args:
            query: Text to search for (case-insensitive).

        Returns:
            List of matching sections with topic and matching lines.
        """
        content = self._read_file()
        if not content:
            return []

        results = []
        query_lower = query.lower()
        lines = content.split("\n")

        current_topic = None
        matches_in_topic: list[str] = []

        for line in lines:
            if re.match(r"^## ", line):
                # Save previous topic matches
                if current_topic and matches_in_topic:
                    results.append(
                        {
                            "topic": current_topic,
                            "matches": matches_in_topic[:5],  # Limit to 5 matches per topic
                            "match_count": len(matches_in_topic),
                        }
                    )
                current_topic = line[3:].strip()
                matches_in_topic = []
            elif current_topic and query_lower in line.lower():
                matches_in_topic.append(line.strip())

        # Don't forget last topic
        if current_topic and matches_in_topic:
            results.append(
                {
                    "topic": current_topic,
                    "matches": matches_in_topic[:5],
                    "match_count": len(matches_in_topic),
                }
            )

        return results


# Global instance
_knowledge_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    """Get the global knowledge store instance."""
    global _knowledge_store
    if _knowledge_store is None:
        # Check for custom path in environment
        custom_path = os.environ.get("U2_KNOWLEDGE_PATH")
        _knowledge_store = KnowledgeStore(custom_path)
    return _knowledge_store
