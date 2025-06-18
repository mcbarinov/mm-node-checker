from datetime import datetime
from typing import Annotated

from mm_base6 import CoreConfig, CoreLifecycle, ServerConfig, SettingsModel, StateModel, setting_field, state_field

from app.core.types import AppCore

core_config = CoreConfig()

server_config = ServerConfig()
server_config.tags = ["node", "check", "proxy"]
server_config.main_menu = {"/nodes": "nodes", "/networks": "networks", "/checks": "checks"}


class Settings(SettingsModel):
    proxies_url: Annotated[str, setting_field("http://localhost:8000", "proxies url, each proxy on new line")]
    limit_concurrent_checks: Annotated[int, setting_field(10, "limit concurrent checks")]
    auto_check: Annotated[bool, setting_field(True, "auto check nodes")]


class State(StateModel):
    proxies: Annotated[list[str], state_field([])]
    proxies_updated_at: Annotated[datetime | None, state_field(None, "timestamp of last proxies update")]


class AppCoreLifecycle(CoreLifecycle[AppCore]):
    async def configure_scheduler(self) -> None:
        self.core.scheduler.add_task("check_next_node", 3, self.core.services.node.check_next)
        self.core.scheduler.add_task("update_proxies", 60, self.core.services.proxy.update)

    async def on_startup(self) -> None:
        """Startup logic for the application."""

    async def on_shutdown(self) -> None:
        """Cleanup logic for the application."""
