from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_cryptocurrency import Network
from mm_jinja.filters import yes_no

from app.core.core import Core


async def header_info(core: Core) -> Markup:
    return Markup(f"auto check: {yes_no(core.dynamic_configs.auto_check)}")  # nosec  # noqa: S704


async def footer_info(_core: Core) -> Markup:
    return Markup("")  # nosec


jinja_config = JinjaConfig(
    header_info=header_info, header_info_new_line=False, footer_info=footer_info, globals={"networks": list(Network)}
)
