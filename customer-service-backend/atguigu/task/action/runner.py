from typing import Dict, Any
from pydantic import BaseModel
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import ActionResult
from atguigu.task.action.registry import ActionRegistry


class ActionCall(BaseModel):
    """定义调用的action的关键要素"""
    action_name: str
    action_kwargs: Dict[str, Any] = {}

class ActionRunner:
    """通过给定的action_call,调用action"""

    def __init__(self, registry: ActionRegistry):
        self.registry = registry

    async def run(self, action_call: ActionCall, state: DialogueState) -> ActionResult:

        # 1,根据action的名字从注册表中获取action
        action_name = action_call.action_name
        action = self.registry.get(action_name) # 拿到action对象

        # 2,调用action
        return await action.run(state, action_call.action_kwargs)