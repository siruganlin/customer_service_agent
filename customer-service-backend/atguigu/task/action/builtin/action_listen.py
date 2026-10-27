import asyncio
from typing import Any, Dict
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class ActionListen(Action):
    """什么都不干，只监听用户的输入"""
    name = "action_listen"

    async def run(self, state: DialogueState, action_kwargs: Dict[str, Any]) -> ActionResult:

        print("action_listen")
        return ActionResult()
