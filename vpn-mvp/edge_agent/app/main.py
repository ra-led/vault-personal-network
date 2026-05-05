import asyncio
import logging
import subprocess
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.state import AgentState, PeerState, load_state, save_state

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="VPN Edge Agent MVP", version="0.1.0")
STATE_FILE = Path("/var/lib/edge-agent/state.json")
state: AgentState = load_state(STATE_FILE)


class PeerCreateIn(BaseModel):
    device_id: int
    public_key: str
    vpn_ip: str


def ensure_internal_auth(x_edge_token: str | None) -> None:
    if not state.token:
        raise HTTPException(status_code=503, detail="Node token not ready")
    if x_edge_token != state.token:
        raise HTTPException(status_code=401, detail="Invalid token")


def run_cmd(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Command failed: {' '.join(cmd)} :: {exc.stderr.strip()}") from exc


async def wait_wireguard_interface(timeout_sec: int = 30) -> None:
    for _ in range(timeout_sec):
        probe = subprocess.run(
            ["wg", "show", settings.wireguard_interface],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return
        await asyncio.sleep(1)
    raise RuntimeError(f"WireGuard interface {settings.wireguard_interface} is not ready")


def peer_apply(peer: PeerState) -> None:
    run_cmd(
        [
            "wg",
            "set",
            settings.wireguard_interface,
            "peer",
            peer.public_key,
            "allowed-ips",
            f"{peer.vpn_ip}/32",
        ]
    )


def peer_remove(peer: PeerState) -> None:
    run_cmd(
        [
            "wg",
            "set",
            settings.wireguard_interface,
            "peer",
            peer.public_key,
            "remove",
        ]
    )


def persist() -> None:
    save_state(STATE_FILE, state)


def parse_transfer() -> dict[str, tuple[int, int]]:
    output = run_cmd(["wg", "show", settings.wireguard_interface, "transfer"])
    if not output:
        return {}
    result: dict[str, tuple[int, int]] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pub_key, rx, tx = parts
        result[pub_key] = (int(rx), int(tx))
    return result


async def register_node() -> None:
    payload = {
        "shared_secret": settings.edge_shared_secret,
        "name": settings.edge_node_name,
        "hostname": settings.edge_hostname,
        "public_ip": settings.edge_public_ip,
        "country_code": settings.edge_country_code,
        "city": settings.edge_city,
        "max_clients": settings.edge_max_clients,
        "agent_version": settings.edge_agent_version,
        "api_url": settings.resolved_edge_agent_url,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{settings.resolved_control_plane_url}/internal/nodes/register", json=payload)
        response.raise_for_status()
        data = response.json()
        state.node_id = data["node_id"]
        state.token = data["token"]
    persist()
    logging.info("registered node id=%s", state.node_id)


def restore_active_peers() -> None:
    for peer in state.peers.values():
        if peer.status == "active":
            peer_apply(peer)
    logging.info("restored active peers=%s", len([p for p in state.peers.values() if p.status == 'active']))


async def heartbeat_loop() -> None:
    last_transfer: dict[str, tuple[int, int]] = {}
    while True:
        if not state.token:
            await asyncio.sleep(3)
            continue

        transfer = parse_transfer()
        usage_rows = []
        for peer in state.peers.values():
            if peer.status != "active":
                continue
            current_rx, current_tx = transfer.get(peer.public_key, (0, 0))
            prev_rx, prev_tx = last_transfer.get(peer.public_key, (0, 0))
            delta_rx = max(0, current_rx - prev_rx)
            delta_tx = max(0, current_tx - prev_tx)
            if delta_rx > 0 or delta_tx > 0:
                usage_rows.append({"device_id": peer.device_id, "rx_bytes": delta_rx, "tx_bytes": delta_tx})
        last_transfer = transfer

        payload = {
            "active_peers": len([p for p in state.peers.values() if p.status == "active"]),
            "tx_bytes": sum(v[1] for v in transfer.values()),
            "rx_bytes": sum(v[0] for v in transfer.values()),
            "cpu_load": 0.1,
            "disk_free_bytes": 10_000_000_000,
        }
        headers = {"X-Node-Token": state.token}
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(f"{settings.resolved_control_plane_url}/internal/nodes/heartbeat", json=payload, headers=headers)
            if usage_rows:
                await client.post(
                    f"{settings.resolved_control_plane_url}/internal/nodes/usage",
                    json={"usages": usage_rows},
                    headers=headers,
                )
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event() -> None:
    await register_node()
    await wait_wireguard_interface()
    restore_active_peers()
    asyncio.create_task(heartbeat_loop())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "node_id": state.node_id, "peers": len(state.peers)}


@app.post("/peers")
def create_peer(payload: PeerCreateIn, x_edge_token: str | None = Header(default=None)) -> dict:
    ensure_internal_auth(x_edge_token)
    existing = state.peers.get(payload.device_id)
    if existing:
        try:
            peer_remove(existing)
        except HTTPException:
            logging.warning("peer remove failed during update, device_id=%s", payload.device_id)
    peer = PeerState(device_id=payload.device_id, public_key=payload.public_key, vpn_ip=payload.vpn_ip, status="active")
    peer_apply(peer)
    state.peers[payload.device_id] = peer
    persist()
    return {"status": "ok"}


@app.delete("/peers/{device_id}")
def delete_peer(device_id: int, x_edge_token: str | None = Header(default=None)) -> dict:
    ensure_internal_auth(x_edge_token)
    peer = state.peers.pop(device_id, None)
    if peer:
        peer_remove(peer)
        persist()
    return {"status": "ok"}


@app.post("/peers/{device_id}/suspend")
def suspend_peer(device_id: int, x_edge_token: str | None = Header(default=None)) -> dict:
    ensure_internal_auth(x_edge_token)
    peer = state.peers.get(device_id)
    if peer and peer.status == "active":
        peer_remove(peer)
        peer.status = "suspended"
        persist()
    return {"status": "ok"}


@app.post("/peers/{device_id}/resume")
def resume_peer(device_id: int, x_edge_token: str | None = Header(default=None)) -> dict:
    ensure_internal_auth(x_edge_token)
    peer = state.peers.get(device_id)
    if peer and peer.status != "active":
        peer_apply(peer)
        peer.status = "active"
        persist()
    return {"status": "ok"}
