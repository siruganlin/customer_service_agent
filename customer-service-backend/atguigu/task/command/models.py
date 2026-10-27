from typing import Any
from pydantic import BaseModel



class Command(BaseModel):
    command: str # 命令字符串
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Command":
        clz = COMMAND_NAME_TO_CLASS[data["command"]]
        return clz(**data)

class StartFlowCommand(Command):
    # 开始任务
    flow: str # 流程id

class SetSlotsCommand(Command):
    # 收集槽位
    slots: dict[str,Any] # 收集槽位信息

class CancelFlowCommand(Command):
    # 取消任务
    pass

class ResumeFlowCommand(Command):
    # 恢复任务
    flow: str | None = None # 流程名字


COMMAND_NAME_TO_CLASS = {
    "start_flow": StartFlowCommand,
    "set_slots": SetSlotsCommand,
    "cancel_flow": CancelFlowCommand,
    "resume_flow": ResumeFlowCommand,
}
