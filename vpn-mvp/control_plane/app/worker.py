import json
import logging
import time
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AuditLog, Device, DeviceStatus, Node
from app.task_queue import QUEUE_KEY, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

PROCESSING_QUEUE_KEY = f"{QUEUE_KEY}:processing"
VISIBILITY_TIMEOUT_SECONDS = 60
RECLAIM_INTERVAL_SECONDS = 5


def _encode_job(job: dict) -> str:
    return json.dumps(job, ensure_ascii=True)


def _decode_job(raw: str) -> dict:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise RuntimeError("Job payload must be a JSON object")
    return parsed


def _extract_job(payload_raw: str) -> dict:
    payload = _decode_job(payload_raw)
    if "delivery_id" in payload and "job" in payload:
        job = payload.get("job")
        if not isinstance(job, dict):
            raise RuntimeError("Delivery payload contains invalid job")
        return job
    return payload


def _claim_job(redis_client) -> tuple[str, dict] | None:
    queue_item_raw = redis_client.brpoplpush(QUEUE_KEY, PROCESSING_QUEUE_KEY, timeout=5)
    if not queue_item_raw:
        return None

    job = _extract_job(queue_item_raw)
    delivery_raw = _encode_job(
        {
            "delivery_id": str(uuid.uuid4()),
            "claimed_at": int(time.time()),
            "job": job,
        }
    )
    # Replace the raw queue item with a delivery envelope carrying visibility metadata.
    pipe = redis_client.pipeline()
    pipe.lrem(PROCESSING_QUEUE_KEY, 1, queue_item_raw)
    pipe.lpush(PROCESSING_QUEUE_KEY, delivery_raw)
    pipe.execute()
    return delivery_raw, job


def _ack_delivery(redis_client, delivery_raw: str) -> None:
    redis_client.lrem(PROCESSING_QUEUE_KEY, 1, delivery_raw)


def _reclaim_expired_inflight(redis_client) -> int:
    reclaimed = 0
    inflight_items = redis_client.lrange(PROCESSING_QUEUE_KEY, 0, -1)
    now = int(time.time())

    for inflight_raw in inflight_items:
        try:
            inflight = _decode_job(inflight_raw)
        except Exception:  # noqa: BLE001
            # Legacy/invalid payload in processing list - recover conservatively.
            if redis_client.lrem(PROCESSING_QUEUE_KEY, 1, inflight_raw):
                redis_client.rpush(QUEUE_KEY, inflight_raw)
                reclaimed += 1
            continue

        if "delivery_id" not in inflight or "job" not in inflight:
            # Legacy payload without delivery envelope - requeue immediately.
            if redis_client.lrem(PROCESSING_QUEUE_KEY, 1, inflight_raw):
                redis_client.rpush(QUEUE_KEY, inflight_raw)
                reclaimed += 1
            continue

        claimed_at = int(inflight.get("claimed_at", 0))
        if now - claimed_at < VISIBILITY_TIMEOUT_SECONDS:
            continue

        job = inflight.get("job")
        if not isinstance(job, dict):
            # Unreadable payload: move raw data back so it is not lost.
            requeue_raw = inflight_raw
        else:
            requeue_raw = _encode_job(job)

        if redis_client.lrem(PROCESSING_QUEUE_KEY, 1, inflight_raw):
            redis_client.rpush(QUEUE_KEY, requeue_raw)
            reclaimed += 1

    return reclaimed


def execute_edge_command(job: dict) -> None:
    node_id = int(job["node_id"])
    method = job["method"]
    path = job["path"]
    payload = job.get("payload", {})

    with SessionLocal() as db:
        node = db.scalar(select(Node).where(Node.id == node_id))
        if not node:
            raise RuntimeError(f"Node not found: {node_id}")
        url = f"{node.api_url}{path}"
        headers = {"X-Edge-Token": node.token}
        with httpx.Client(timeout=10.0) as client:
            response = client.request(method=method, url=url, json=payload, headers=headers)
        if response.status_code >= 300:
            raise RuntimeError(f"Edge command failed ({response.status_code}): {response.text}")


def apply_post_success(job: dict) -> None:
    post_success = job.get("post_success")
    if not post_success:
        return

    if post_success.get("type") != "device_status":
        raise RuntimeError(f"Unknown post_success type: {post_success.get('type')}")

    device_id = int(post_success["device_id"])
    target_status = DeviceStatus(post_success["status"])

    with SessionLocal() as db:
        device = db.get(Device, device_id)
        if not device:
            raise RuntimeError(f"Device not found for post_success: {device_id}")
        if device.status != target_status:
            device.status = target_status
            if target_status == DeviceStatus.deleted and device.revoked_at is None:
                device.revoked_at = datetime.now(UTC)
            db.commit()


def requeue_job(job: dict, next_attempt: int, max_attempts: int, skip_edge: bool) -> None:
    retry_job = {
        "job_type": "edge_command",
        "node_id": int(job["node_id"]),
        "method": job["method"],
        "path": job["path"],
        "payload": job.get("payload", {}),
        "attempt": next_attempt,
        "max_attempts": max_attempts,
    }

    if job.get("post_success"):
        retry_job["post_success"] = job["post_success"]

    if skip_edge:
        retry_job["skip_edge"] = True

    get_redis().lpush(QUEUE_KEY, json.dumps(retry_job, ensure_ascii=True))


def handle_job(job: dict) -> None:
    if job.get("job_type") != "edge_command":
        logging.warning("Unknown job type: %s", job.get("job_type"))
        return

    skip_edge = bool(job.get("skip_edge", False))
    attempt = int(job.get("attempt", 1))
    max_attempts = int(job.get("max_attempts", 5))

    try:
        if not skip_edge:
            execute_edge_command(job)
            # edge command is already applied; retry only DB side-effect on subsequent attempts.
            skip_edge = bool(job.get("post_success"))

        apply_post_success(job)

        logging.info(
            "edge command done node_id=%s method=%s path=%s attempt=%s skip_edge=%s",
            job.get("node_id"),
            job.get("method"),
            job.get("path"),
            attempt,
            bool(job.get("skip_edge", False)),
        )
    except Exception as exc:  # noqa: BLE001
        if attempt < max_attempts:
            next_attempt = attempt + 1
            backoff = min(2**attempt, 30)
            logging.warning(
                "edge command failed, retry scheduled in %ss, attempt=%s/%s error=%s",
                backoff,
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(backoff)
            requeue_job(job, next_attempt=next_attempt, max_attempts=max_attempts, skip_edge=skip_edge)
        else:
            logging.error("edge job permanently failed: %s", exc)
            with SessionLocal() as db:
                db.add(
                    AuditLog(
                        actor_type="worker",
                        actor_id="edge-command",
                        entity_type="node",
                        entity_id=str(job.get("node_id")),
                        action="edge_command_failed",
                        payload_json={"job": job, "error": str(exc)},
                    )
                )
                db.commit()


def main() -> None:
    redis_client = get_redis()
    logging.info(
        "worker started, queue=%s processing=%s visibility_timeout=%ss",
        QUEUE_KEY,
        PROCESSING_QUEUE_KEY,
        VISIBILITY_TIMEOUT_SECONDS,
    )
    last_reclaim_at = 0.0

    while True:
        now = time.monotonic()
        if now - last_reclaim_at >= RECLAIM_INTERVAL_SECONDS:
            reclaimed = _reclaim_expired_inflight(redis_client)
            if reclaimed:
                logging.warning("reclaimed %s expired in-flight job(s)", reclaimed)
            last_reclaim_at = now

        claimed = _claim_job(redis_client)
        if not claimed:
            continue

        delivery_raw, job = claimed
        try:
            handle_job(job)
        except Exception:  # noqa: BLE001
            logging.exception("unexpected error while handling delivery")
            continue

        _ack_delivery(redis_client, delivery_raw)


if __name__ == "__main__":
    main()
