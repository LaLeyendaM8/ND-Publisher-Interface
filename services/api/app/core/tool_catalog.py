from app.core.schemas import ToolId


TOOL_CATALOG: list[dict[str, str]] = [
    {
        "id": "translation",
        "name": "Book Translation",
        "description": "Translate philosophical text chunks DE -> ES with glossary locking.",
    },
    {
        "id": "bibliography",
        "name": "Bibliography Processing",
        "description": "Preserve bibliography structure and only add German-title translations.",
    },
    {
        "id": "proofcheck",
        "name": "Mechanical Lektorat",
        "description": "Detect grammar, orthography, punctuation, and spacing issues.",
    },
]


def get_tool_by_id(tool_id: ToolId) -> dict[str, str]:
    for tool in TOOL_CATALOG:
        if tool["id"] == tool_id:
            return tool
    raise KeyError(f"Unknown tool: {tool_id}")
