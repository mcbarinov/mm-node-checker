from markupsafe import Markup
from mm_base6 import JinjaConfig
from mm_crypto_utils import Network

from app.core.core import Core


async def header_info(_core: Core) -> Markup:
    return Markup("")  # nosec


async def footer_info(_core: Core) -> Markup:
    return Markup("")  # nosec


jinja_config = JinjaConfig(
    header_info=header_info, header_info_new_line=False, footer_info=footer_info, globals={"networks": list(Network)}
)
