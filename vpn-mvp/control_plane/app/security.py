import base64
import secrets

from cryptography.fernet import Fernet

from app.config import get_settings


settings = get_settings()


def _get_fernet() -> Fernet:
    key = settings.fernet_key
    if not key or key == 'replace_me_fernet_key':
        raise RuntimeError('FERNET_KEY must be configured for production-safe key storage')
    try:
        base64.urlsafe_b64decode(key.encode())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError('FERNET_KEY is not valid urlsafe base64') from exc
    return Fernet(key.encode())


def encrypt_secret(raw_value: str) -> str:
    return _get_fernet().encrypt(raw_value.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def random_token(size: int = 24) -> str:
    return secrets.token_urlsafe(size)
