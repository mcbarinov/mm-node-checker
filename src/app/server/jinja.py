from typing import override

from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_jinja.filters import yes_no
from mm_web3 import Network

from app.core.types import AppCore


class AppJinjaConfig(JinjaConfig[AppCore]):
    filters = {}
    globals = {"networks": list(Network)}

    @override
    async def header_status(self) -> Markup:
        return Markup("auto check: {}").format(yes_no(self.core.settings.auto_check))
