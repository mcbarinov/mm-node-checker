from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_jinja.filters import yes_no
from mm_web3 import Network

from app.core.types import AppCore


async def header_info(core: AppCore) -> Markup:
    return Markup(f"auto check: {yes_no(core.dynamic_configs.auto_check)}")  # nosec  # noqa: S704


async def footer_info(_core: AppCore) -> Markup:
    return Markup("")  # nosec


jinja_config = JinjaConfig(
    header_info=header_info, header_info_new_line=False, footer_info=footer_info, globals={"networks": list(Network)}
)
