"""Jinja2 template configuration."""

from typing import Any, override

from markupsafe import Markup
from mm_base6 import BaseJinjaConfig
from mm_jinja.filters import yes_no
from mm_web3 import Network

from app.core.types import AppCore


class JinjaConfig(BaseJinjaConfig[AppCore]):
    """Application-specific Jinja configuration."""

    @override
    def get_globals(self) -> dict[str, Any]:
        return {"networks": list(Network)}

    @override
    async def header_status(self) -> Markup:
        """Return status text for the page header."""
        return Markup("auto check: {}").format(yes_no(self.core.settings.auto_check))
