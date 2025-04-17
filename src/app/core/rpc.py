import logging

import pydash
from mm_std import Result, http_request

logger = logging.getLogger(__name__)


async def get_evm_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_error():
        return res.to_result_err()
    try:
        return res.to_result_ok(int(res.parse_json_body("result"), 16))
    except Exception as e:
        return res.to_result_err(e)


async def get_starknet_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "starknet_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_error():
        return res.to_result_err()
    try:
        return res.to_result_ok(res.parse_json_body("result"))
    except Exception as e:
        return res.to_result_err(e)


async def get_solana_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "getBlockHeight", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_error():
        return res.to_result_err()
    json_body = res.parse_json_body()
    err = pydash.get(json_body, "error.message")
    if err:
        return res.to_result_err(f"service_error: {err}")
    try:
        return res.to_result_ok(int(json_body["result"]))
    except Exception as e:
        return res.to_result_err(e)


async def get_aptos_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    res = await http_request(
        url=url,
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_error():
        return res.to_result_err()
    try:
        return res.to_result_ok(int(res.parse_json_body()["block_height"]))
    except Exception as e:
        return res.to_result_err(e)
