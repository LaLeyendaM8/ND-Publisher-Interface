from fastapi import APIRouter

from app.core.tool_catalog import TOOL_CATALOG


router = APIRouter()


@router.get("")
def list_tools() -> dict[str, list[dict[str, str]]]:
    return {"tools": TOOL_CATALOG}
