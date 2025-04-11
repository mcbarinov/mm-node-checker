import logging

from mm_std import Err, Ok, Result, hra

logger = logging.getLogger(__name__)


async def get_evm_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await hra(
        url=url,
        method="post",
        params={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if isinstance(res, Err):
        return res
    try:
        return Ok(int(res.json["result"], 16), data=res.to_dict())
    except Exception as e:
        return Err("error", {"exception": str(e), "response": res.to_dict()})


async def get_starknet_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await hra(
        url=url,
        method="post",
        params={"jsonrpc": "2.0", "method": "starknet_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if isinstance(res, Err):
        return res
    try:
        return Ok(int(res.json["result"]), data=res.to_dict())
    except Exception as e:
        return Err("error", {"exception": str(e), "response": res.to_dict()})


async def get_solana_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await hra(
        url=url,
        method="post",
        params={"jsonrpc": "2.0", "method": "getBlockHeight", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if isinstance(res, Err):
        return res
    err = res.json.get("error", {}).get("message", "")
    if err:
        return res.to_err_result(f"service_error: {err}")
    try:
        return Ok(int(res.json["result"]), data=res.to_dict())
    except Exception as e:
        return Err("error", {"exception": str(e), "response": res.to_dict()})


async def get_aptos_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await hra(
        url=url,
        proxy=proxy,
        timeout=timeout,
    )
    if isinstance(res, Err):
        return res
    try:
        return Ok(int(res.json["block_height"]), data=res.to_dict())
    except Exception as e:
        return Err("error", {"exception": str(e), "response": res.to_dict()})
