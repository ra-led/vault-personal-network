import json
from typing import Any

from redis import Redis

from app.config import get_settings

settings = get_settings()
QUEUE_KEY = "vpn:jobs:edge_commands"


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_edge_command(
    *,
    node_id: int,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    post_success: dict[str, Any] | None = None,
    attempt: int = 1,
    max_attempts: int = 5,
) -> None:
    job = {
        "job_type": "edge_command",
        "node_id": node_id,
        "method": method,
        "path": path,
        "payload": payload or {},
        "attempt": attempt,
        "max_attempts": max_attempts,
    }
    if post_success:
        job["post_success"] = post_success
    get_redis().lpush(QUEUE_KEY, json.dumps(job, ensure_ascii=True))
