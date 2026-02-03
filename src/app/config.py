"""Application configuration: settings and state definitions."""

from datetime import datetime
from typing import Annotated

from mm_base6 import BaseSettings, BaseState, Config, setting_field, state_field

config = Config(  # ty: ignore[missing-argument]  # pydantic-settings loads from env vars
    openapi_tags=["node", "check", "proxy"], ui_menu={"/nodes": "nodes", "/networks": "networks", "/checks": "checks"}
)


class Settings(BaseSettings):
    """User-configurable application settings."""

    proxies_url: Annotated[str, setting_field("http://localhost:8000", "proxies url, each proxy on new line")]
    limit_concurrent_checks: Annotated[int, setting_field(10, "limit concurrent checks")]
    auto_check: Annotated[bool, setting_field(True, "auto check nodes")]


class State(BaseState):
    """Runtime application state."""

    proxies: Annotated[list[str], state_field([])]
    proxies_updated_at: Annotated[datetime | None, state_field(None, "timestamp of last proxies update")]
