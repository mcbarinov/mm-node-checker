from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_jinja.filters import yes_no
from mm_web3 import Network

from app.core.types import AppCore


class AppJinjaConfig(JinjaConfig[AppCore]):
    filters = {}
    globals = {"networks": list(Network)}
    header_info_new_line = False

    async def header(self) -> Markup:
        return Markup(f"auto check: {yes_no(self.core.settings.auto_check)}")  # nosec  # noqa: S704
