import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class PeerState:
    device_id: int
    public_key: str
    vpn_ip: str
    status: str = "active"


@dataclass
class AgentState:
    node_id: int | None = None
    token: str | None = None
    peers: dict[int, PeerState] = field(default_factory=dict)


def load_state(path: Path) -> AgentState:
    if not path.exists():
        return AgentState()
    raw = json.loads(path.read_text(encoding="utf-8"))
    peers = {
        int(k): PeerState(
            device_id=int(v["device_id"]),
            public_key=v["public_key"],
            vpn_ip=v["vpn_ip"],
            status=v.get("status", "active"),
        )
        for k, v in raw.get("peers", {}).items()
    }
    return AgentState(node_id=raw.get("node_id"), token=raw.get("token"), peers=peers)


def save_state(path: Path, state: AgentState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "node_id": state.node_id,
        "token": state.token,
        "peers": {str(k): asdict(v) for k, v in state.peers.items()},
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
