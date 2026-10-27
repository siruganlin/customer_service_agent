import asyncio
import json
from abc import abstractclassmethod, ABC
from typing import Any

from pydantic import BaseModel

from atguigu.domain.state import DialogueState
from atguigu.infrastructure.shered import fetch_product, fetch_order, fetch_logistics


class KnowledgeChunk(BaseModel ):
    content: str


class KnowledgeProvider(ABC):

    provider_id = ""

    @abstractclassmethod
    async def retrieve(self, state: DialogueState ) -> list[KnowledgeChunk]:
        """
        信息检索的方法
        :return:
        """
        pass

class ProductAPIProvider(KnowledgeProvider):

    provider_id = "api.product"

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        # 目前只能接受对象消息
        product_id = state.focused_object.id
        data: dict[str, Any] = await fetch_product(product_id)

        text = json.dumps(data, ensure_ascii=False, indent=4)

        return [KnowledgeChunk(content=f"商品信息：\n {text}")]

class OderAPIProvider(KnowledgeProvider):

    provider_id = "api.order"

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:

        order_number = state.focused_object.id

        # 并发调用：fetch_order和fetch_logistics
        order_data, logistics_data = await asyncio.gather(
            fetch_product(order_number),
            fetch_order(order_number),
        )

        text = json.dumps(
            {"order_number": order_number,
             "order": order_data,
             "logistics": logistics_data},
            ensure_ascii=False,
            indent=4,
        )

        return [
            KnowledgeChunk(content=f"订单信息\n {text}")
        ]

class FAQProvider(KnowledgeProvider):

    provider_id = "faq.default"
    # TODO 集成 mysql\mongodb\Elasticsearch
    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        return [KnowledgeChunk(content="FAQ:未检索到信息")]

class RAGProvider(KnowledgeProvider):

    provider_id = "rag.default"

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:

        # TODO 集成milvus
        return [KnowledgeChunk(content="RAG:未检索到信息")]