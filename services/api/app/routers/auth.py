from fastapi import APIRouter, Depends

from app.core.actor import RequestActor, require_actor


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/sync")
def sync_actor(actor: RequestActor = Depends(require_actor)) -> dict[str, object]:
    return {
        "ok": True,
        "actor": {
            "user_id": actor.user_id,
            "email": actor.email,
            "role": actor.role,
            "workspace_id": actor.workspace_id,
        },
    }
