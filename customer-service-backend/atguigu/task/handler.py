from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.runner import ActionRunner
from atguigu.task.command.models import Command
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.flows import FlowsList


class TaskHandler:

    def __init__(self,flows: FlowsList,command_processor: CommandProcessor, action_runner: ActionRunner,flow_executor: FlowExecutor):
        self.flows = flows
        self.command_processor = command_processor
        self.action_runner = action_runner
        self.flow_executor = flow_executor

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:

        # 阶段一： 修改state的状态信息(CommandProcessor)
        self.command_processor.run(commands,state,self.flows)

        # 阶段二： 推进流程,生成客服回复(FlowsExecutor,Action)
        messages: list[BotMessage] = await self.flow_executor.run_task(state, self.flows, self.action_runner)

        return messages

