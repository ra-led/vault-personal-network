from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.edge", env_file_encoding="utf-8", extra="ignore")

    edge_agent_port: int = 8081
    edge_node_name: str = "edge-ru-1"
    edge_public_ip: str = "203.0.113.10"
    edge_hostname: str = "edge-ru-1.local"
    edge_country_code: str = "RU"
    edge_city: str = "Moscow"
    edge_max_clients: int = 300
    edge_agent_version: str = "0.1.0"
    edge_agent_url: str = "auto"
    control_plane_url: str = "https://control.example.com"
    edge_shared_secret: str = "dev-secret"
    wireguard_interface: str = "wg0"
    wireguard_subnet: str = "10.66.0.0/24"

    @property
    def resolved_edge_agent_url(self) -> str:
        if self.edge_agent_url and self.edge_agent_url.lower() != "auto":
            return self.edge_agent_url.rstrip("/")
        return f"http://{self.edge_public_ip}:{self.edge_agent_port}"

    @property
    def resolved_control_plane_url(self) -> str:
        return self.control_plane_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
