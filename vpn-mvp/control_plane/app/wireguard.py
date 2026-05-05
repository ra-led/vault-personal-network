import base64
import io
import ipaddress
from dataclasses import dataclass

import qrcode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

from app.config import get_settings


settings = get_settings()


@dataclass
class ClientKeys:
    private_key: str
    public_key: str


def generate_client_keys() -> ClientKeys:
    private_key_obj = x25519.X25519PrivateKey.generate()
    public_key_obj = private_key_obj.public_key()

    private_raw = private_key_obj.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key_obj.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return ClientKeys(
        private_key=base64.b64encode(private_raw).decode(),
        public_key=base64.b64encode(public_raw).decode(),
    )


def pick_next_vpn_ip(used_ips: set[str], subnet: str = '10.66.0.0/24') -> str:
    network = ipaddress.ip_network(subnet)
    for host in network.hosts():
        candidate = str(host)
        if candidate.endswith('.1'):
            continue
        if candidate not in used_ips:
            return candidate
    raise RuntimeError('No available VPN IP addresses')


def build_client_conf(private_key: str, vpn_ip: str) -> str:
    return (
        '[Interface]\n'
        f'PrivateKey = {private_key}\n'
        f'Address = {vpn_ip}/32\n'
        f'DNS = {settings.wg_dns}\n\n'
        '[Peer]\n'
        f'PublicKey = {settings.server_public_key}\n'
        f'Endpoint = {settings.wg_endpoint}\n'
        f'AllowedIPs = {settings.wg_allowed_ips}\n'
        f'PersistentKeepalive = {settings.wg_keepalive}\n'
    )


def conf_to_qr_base64(conf_text: str) -> str:
    image = qrcode.make(conf_text)
    buff = io.BytesIO()
    image.save(buff, format='PNG')
    return base64.b64encode(buff.getvalue()).decode()
