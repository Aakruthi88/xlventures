"""
Playbook Tool
=============
LangChain tool to fetch operational playbook document contents.
"""

import os
from pathlib import Path
from langchain.tools import tool


@tool
def get_playbook(playbook_name: str) -> str:
    """
    Fetch the complete text content of an enterprise playbook or guide by filename
    (e.g., 'renewal_playbook.md', 'customer_success_sop.md').

    Args:
        playbook_name: Name of the playbook file (e.g., 'renewal_playbook.md').

    Returns:
        The content of the playbook as a string, or an error message if not found.
    """
    try:
        data_dir = Path(__file__).resolve().parents[3] / "data" / "knowledge_base"
        file_path = data_dir / playbook_name

        if file_path.exists() and file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # Try to list available playbooks for helpful feedback
            available = [f.name for f in data_dir.glob("*.md")]
            return f"Playbook '{playbook_name}' not found. Available options: {available}"
    except Exception as e:
        return f"Error reading playbook: {e}"
