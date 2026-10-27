# atguigu/task/command/processor.py
from atguigu.domain.contexts import StartedSystemContext, InterruptedSystemContext, ResumedSystemContext, \
    CanceledSystemContext, TaskContext
from atguigu.domain.state import DialogueState
from atguigu.task.command.models import Command, StartFlowCommand, SetSlotsCommand, ResumeFlowCommand, CancelFlowCommand
from atguigu.task.flow.flows import FlowsList


class CommandProcessor:

    def run(self, commands: list[Command], state: DialogueState, flows: FlowsList) -> None:

        """将命令应用到state"""

        for command in commands:
            self._apply(command, state, flows)

    def _apply(self, command: Command, state: DialogueState, flows: FlowsList) -> None:

        """处理每个命令"""

        if isinstance(command, StartFlowCommand):

            self._handle_start_flow(command,state,flows)

        elif isinstance(command, SetSlotsCommand):

            self._handle_set_slots(command, state)

        elif isinstance(command, CancelFlowCommand):

            self._handle_cancel_flow(state, flows)

        elif isinstance(command, ResumeFlowCommand):

            self._handle_resume_flow(command, state, flows)

    @staticmethod
    def _readable_flow_name(flow_id: str, flows: FlowsList) -> str:
        """根据flow_id获取flow_name"""

        flow = flows.get_flow_by_id(flow_id)
        return flow.name if flow else flow_id

    @staticmethod
    def _activate_started_system_flow(
            state: DialogueState,
            flows: FlowsList,
            started_flow_id: str,
            started_flow_name: str
    ):
        """"
        激活开始流程的过场白
        """

        flow = flows.get_flow_by_id("system_task_started")
        state.start_active_system_task(StartedSystemContext(
            # flow_id
            step_id = flow.start_step().id,
            started_flow_id = started_flow_id,
            started_flow_name = started_flow_name
        ))

    @staticmethod
    def _activate_interrupted_system_flow(
            state: DialogueState,
            flows: FlowsList,
            interrupted_flow_id: str,
            interrupted_flow_name: str,
            started_flow_id: str,
            started_flow_name: str
    ):
        """"
        激活打断流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_interrupted")
        state.start_active_system_task(InterruptedSystemContext(
            # flow_id=flow.id,
            step_id=flow.start_step().id,
            interrupted_flow_id=interrupted_flow_id,
            interrupted_flow_name=interrupted_flow_name,
            started_flow_id=started_flow_id,
            started_flow_name=started_flow_name
        ))

    @staticmethod
    def _activate_resumed_system_flow(
            state: DialogueState,
            flows: FlowsList,
            resumed_flow_id: str,
            resumed_flow_name: str
    ):
        """"
        激活恢复流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_resumed")
        state.start_active_system_task(ResumedSystemContext(
            # flow_id=flow.id,
            step_id=flow.start_step().id,
            resumed_flow_id=resumed_flow_id,
            resumed_flow_name=resumed_flow_name
        ))

    @staticmethod
    def _activate_canceled_system_flow(
            state: DialogueState,
            flows: FlowsList,
            canceled_flow_id: str,
            canceled_flow_name: str
    ):
        """"
        激活取消流程的过场白
        """
        flow = flows.get_flow_by_id("system_task_canceled")
        state.start_active_system_task(CanceledSystemContext(
            # flow_id=flow.id,
            step_id=flow.start_step().id,
            canceled_flow_id=canceled_flow_id,
            canceled_flow_name=canceled_flow_name
        ))

    def _handle_start_flow(self, command: StartFlowCommand, state: DialogueState, flows: FlowsList):

        # ================清除系统过场 + 校验=================
        # 1. 清除当前系统过场
        state.end_active_system_task()

        # 2. 防御性编程：不允许直接执行系统任务
        if command.flow.startswith("system_"): # startswith；检查command.flow的前缀是不是已system_开头
            raise ValueError(f"不能启动系统流程:{command.flow}")

        # 3. 防御性编程：流程必须存在
        target_flow = flows.get_flow_by_id(command.flow)
        if target_flow is None:
            raise ValueError(f"未知流程:{command.flow}")

        # 4. 防御性编程：流程必须有起点
        start_step = target_flow.start_step()
        if start_step is None:
            raise ValueError(f"流程:{command.flow} 没有开始步骤")

        # ================激活业务任务和系统流程： 有active_task的情况=================

        # 获取active_task
        active_task = state.active_task
        if active_task is not None:

            # 分支1：同一个流程，不重复启动
            if active_task.flow_id == command.flow:
                return

            # 分支2、3：不是同一个流程
            # 将当前的激活任务放入暂停栈中
            state.interrupted_active_task()

            # 分支3（假设任务在暂停栈）：试着从暂停任务中恢复当前要开始的任务，返回是否恢复成功
            resumed = state.resumed_active_task(command.flow)
            if not resumed:
                # 分支2：开启新任务
                state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))


            # 激活系统流程(打断过场)
            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(interrupted_flow_id, flows)
            started_flow_id = command.flow
            started_flow_name = self._readable_flow_name(started_flow_id, flows)
            self._activate_interrupted_system_flow(
                state, flows,
                interrupted_flow_id, interrupted_flow_name,
                started_flow_id,started_flow_name
            )

            return

        # ================激活业务任务和系统流程： 没有active_task的情况=================

        # 分支4：试着从暂停任务中恢复当前要开始的任务，返回是否恢复成功
        resumed = state.resumed_active_task()
        if resumed:
            # 激活系统流程(恢复过场)
            resumed_flow_id = command.flow
            resumed_flow_name = self._readable_flow_name(resumed_flow_id, flows)
            self._activate_resumed_system_flow(
                state, flows,
                resumed_flow_id, resumed_flow_name
            )

            return

        # 分支5：开始全新的流程
        # 激活业务流程
        state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))
        # 激活系统过场
        started_flow_id = command.flow
        started_flow_name = self._readable_flow_name(started_flow_id, flows)
        self._activate_started_system_flow(
            state, flows, started_flow_id, started_flow_name
        )

    # 没有active_task 则激活一个新任务
    def _handle_start_flow_v1(self, command: StartFlowCommand, state: DialogueState, flows: FlowsList):

        # 1. 激活业务任务
        flow_id = command.flow
        target_flow = flows.get_flow_by_id(flow_id)
        start_step = target_flow.start_step()
        state.start_active_task(TaskContext(flow_id=flow_id, step_id=start_step.id))

        # 2. 激活系统流程
        self._activate_started_system_flow(
            state, flows, flow_id, self._readable_flow_name(flow_id=flow_id, flows=flows)
        )

    def _handle_set_slots(self, command: SetSlotsCommand, state: DialogueState):
        if state.active_task:
            state.set_slots(command.slots)

    def _handle_cancel_flow(self, state: DialogueState, flows: FlowsList):

        # 1，获取当前的流程
        active_task = state.active_task

        # 2，取消当前激活的流程
        state.cancel_active_task()

        # 3，添加取消的系统个过场
        canceled_flow_id = active_task.flow_id
        canceled_flow_name = self._readable_flow_name(canceled_flow_id,flows)
        self._activate_canceled_system_flow(
            state, flows,
            canceled_flow_id,canceled_flow_name
        )

    def _handle_resume_flow(self, command: ResumeFlowCommand, state: DialogueState, flows: FlowsList):

        # ===================阶段1：找到要恢复的流程===================
        if command.flow is not None:
            # 指名恢复:用户明确说了恢复哪个
            target_flow = flows.get_flow_by_id(command.flow)
            if target_flow is None:
                raise ValueError(f"未知流程 {command.flow}")

            # 确定要恢复的任务
            target_flow_id = command.flow
            target_flow_name = target_flow.name
        else:
                # 不指名恢复:用户只说"继续刚才的" → 取暂停栈栈顶(最近挂起的)
            if not state.paused_tasks:
                return

            # 确定要恢复的任务
            top_paused = state.paused_tasks[-1]
            target_flow_id = top_paused.flow_id
            target_flow_name = self._readable_flow_name(target_flow_id, flows)

        # ===================阶段2：恢复流程 ===================

        # 获取激活的任务
        active_task = state.active_task

        # 有激活任务
        if active_task is not None:

            # 分支1：有活跃任务，并且活跃任务就是要恢复的任务
            if active_task.flow_id == target_flow_id:
                return

            # 获取要被打断的任务的基本信息
            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(interrupted_flow_id, flows)

            # 将当前任务放在paused列表中
            state.interrupted_active_task()

            # 分支2：恢复目标任务失败
            if not state.resumed_active_task(target_flow_id):
                # 当恢复失败的时候，做回退（撤销interrupt）
                state.resumed_active_task()
                return

            # 分支3：激活interrupted过场
            self._activate_interrupted_system_flow(
                state, flows,
                interrupted_flow_id, interrupted_flow_name,
                target_flow_id, target_flow_name
            )

        # 没有激活任务
        else:

            # 如果恢复失败则退出（例如，用户指定了一个没有挂起的任务）
            if not state.resumed_active_task(target_flow_id):
                return

            # 分支4：激活恢复任务的系统过场
            self._activate_resumed_system_flow(
                state, flows,
                target_flow_id, target_flow_name
            )

