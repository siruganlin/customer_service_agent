# 注册表: 把这些可能用到的方法先创建出来放到键值对中，要用的时候直接调用注册表就可以
from typing import List

from atguigu.knowledge.provider import KnowledgeProvider, KnowledgeChunk


class KnowledgeProviderRegistry:
    """只是提供注册表"""

    def __init__(self, providers: List[KnowledgeProvider]):
        self._providers_by_id = {p.provider_id: p for p in providers}

    def get(self, provider_id: str) -> KnowledgeProvider:

        return self._providers_by_id[provider_id]
