from typing import Dict

from atguigu.task.action.base import Action


class ActionRegistry:

    def __init__(self):
        # Dict：键是action的名字,值是action对象本身
        self._actions: Dict[str, Action] = {}

    # 注册action 动态调用register方法给_actions里面赋值，就注册好了
    def register(self, action: Action) -> None:
        self._actions[action.name] = action

    # 获取action
    def get(self, name: str) -> Action:
        if name not in self._actions:
            raise KeyError(f"未知Action {name}")
        return self._actions[name]