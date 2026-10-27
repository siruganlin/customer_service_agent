from typing import Dict
from urllib.parse import quote

from atguigu.conf.config import settings
from atguigu.infrastructure import http_client

def _base_url() -> str:
    """处理url的/"""
    return settings.commerce_api_base_url.rstrip("/")

def _extract_data(result: dict | None) -> dict | None:
    """"获取出结果中的的data字段"""
    data = result.get("data") if isinstance(result, dict) else None
    return data if isinstance(data, dict) else None

async def fetch_order(order_id: str) -> Dict | None:
    """获取订单信息"""

    try:
        # 1,调用API
        result = await http_client.http_client.get(f'{_base_url()}/orders/{quote(order_id,safe="")}')

        # 2,解析data
        return _extract_data(result.json())

    except Exception:
        return None

async def fetch_logistics(order_id: str) -> Dict | None:
    """获取物流信息"""

    try:
        # 1,调用API
        result = await http_client.http_client.get(f'{_base_url()}/orders/{quote(order_id,safe="")}/logistics')

        # 2，解析data
        return _extract_data(result.json()
)

    except Exception:
        return None

async def fetch_product(product_id: str) -> Dict | None:
    """获取商品信息"""

    try:
        # 1,调用API
        result = await http_client.http_client.get(f'{_base_url()}/products/{quote(product_id,safe="")}')

        # 2，解析data
        return _extract_data(result.json()
)

    except Exception:
        return None

async def submit_refund_request(order_id: str) -> Dict | None:
    """退款申请"""
    try:
        # 1，调用API
        result = await http_client.http_client.get(f'{_base_url()}/orders/{quote(order_id,safe="")}/ refund - applications')

        # 2，解析data
        return _extract_data(result.json()
)
    except Exception:
        return None
