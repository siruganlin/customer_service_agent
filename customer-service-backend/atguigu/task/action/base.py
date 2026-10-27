from abc import ABC, abstractmethod
from typing import List, Dict, Any

from pydantic import BaseModel

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState


class ActionResult(BaseModel):
    """action的返回值"""
    message: List[BotMessage] = []
    slot_updates: Dict[str, Any] = {}

class Action(ABC):
    """action的抽象基类"""
    name: str # action的名字

    @abstractmethod
    async def run(self, state: DialogueState,action_kwargs: Dict[str, Any]) -> ActionResult:
        """调用中台接口查询"""
        pass