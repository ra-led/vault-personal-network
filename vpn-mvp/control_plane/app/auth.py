from fastapi import Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Node

settings = get_settings()


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    if not settings.internal_api_token:
        raise HTTPException(status_code=500, detail="INTERNAL_API_TOKEN is not configured")
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="Invalid internal token")


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.admin_api_token:
        raise HTTPException(status_code=500, detail="ADMIN_API_TOKEN is not configured")
    if x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")


def get_node_by_token_for_node(
    db: Session,
    *,
    node_id: int,
    x_node_token: str | None,
) -> Node:
    if not x_node_token:
        raise HTTPException(status_code=401, detail="Missing node token")
    node = db.scalar(select(Node).where(Node.id == node_id, Node.token == x_node_token))
    if not node:
        raise HTTPException(status_code=401, detail="Invalid node token")
    return node
