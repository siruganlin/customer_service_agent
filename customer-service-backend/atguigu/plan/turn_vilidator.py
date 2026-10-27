from typing import Dict

from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.plan.models import TurnPlanValidationResult, TurnPlan, ClarifyReason
from atguigu.task.command.models import StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand
from atguigu.task.flow.flows import FlowsList


class TurnPlanValidator:

    def validate(self,
                 turn_plan: TurnPlan,
                 flow_list:FlowsList,
                 state: DialogueState, intents: Dict[str,KnowledgeIntent]) -> TurnPlanValidationResult:

        # 1,获取当前激活的轨道
        active_tracks = self._active_tracks(turn_plan)

        # 2，判断是否没有命中轨道
        if not active_tracks:
            return self._reject(ClarifyReason.MISSING_TRACK)

        # 3,判断是否命中了多条轨道
        if len(active_tracks) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TRACKS)

        # 4, 获取命中的一个轨道
        active_track = active_tracks[0]

        # 5,判断是那条轨道
        # 5.1业务流程
        # list元素完全一致才是True
        if active_tracks == ["task"]:
            return self._validate_task(turn_plan, flow_list)

        # 5.2 知识
        if active_tracks == ["knowledge"]:
            return self._validate_knowledge(turn_plan, state, intents)

        # 校验通过
        return TurnPlanValidationResult(valid=True)

    @staticmethod
    def _active_tracks( turn_plan: TurnPlan) -> list[str]:


        active_tracks: list[str] = []
        if turn_plan.task is not None:
            active_tracks.append("task")
        if turn_plan.knowledge is not None:
            active_tracks.append("knowledge")
        if turn_plan.chitchat is not None:
            active_tracks.append("chitchat")

        return active_tracks

    @staticmethod
    def _reject(reason: ClarifyReason) -> TurnPlanValidationResult:

        return TurnPlanValidationResult(valid=False,reason=reason)

    def _validate_task(self, turn_plan: TurnPlan, flow_list: FlowsList):
        """
        task轨道的四重判断
        :param turn_plan:
        :param flow_list:
        :return:
        """
        # 获取task_plan
        task_plan = turn_plan.task

        # 第一重：判断command不能为空
        if not task_plan.commands:
            return self._reject(ClarifyReason.MISSING_TASK_COMMANDS )

        # 第二重： 模型编了一个commands
        allowed = (StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand)
        # all : commands遍历完了之后每一轮返回都为：True则为True，有一轮为False则为False
        if not all(isinstance(cmd, allowed) for cmd in task_plan.commands):
                return self._reject(ClarifyReason.INVALID_TASK_COMMANDS )

        # 第三重：不能同时开启多个任务
        start_commands = [cmd for cmd in task_plan.commands if isinstance(cmd, StartFlowCommand)]
        if len(start_commands) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TASK_FLOWS)

        # 第四重：模型编了一个Flow
        if start_commands:
            flow_name = start_commands[0].flow
            flow = flow_list.get_flow_by_id(flow_name)
            if flow is None:
                return self._reject(ClarifyReason.UNKNOWN_TASK_FLOW)
        return TurnPlanValidationResult(valid=True)

    def _validate_knowledge(self,
                turn_plan: TurnPlan,
                state: DialogueState,
                intents: KnowledgeIntent
                ) -> TurnPlanValidationResult:

        # 1，获取knowledge_plan轨道
        knowledge_plan = turn_plan.knowledge

        # 2,第一重：模型没有识别出意图
        if not knowledge_plan.intents:
            return self._reject(ClarifyReason.MISSING_KNOWLEDGE_INTENT)

        # 3, 第二重：判断用户点击的对象是否和模型识别出来的意图一致
        focused_object = state.focused_object
        for intent in knowledge_plan.intents:
            # 获取元数据
            intent_mate = intents[intent]
            requires_object = intent_mate.requires_object
            if requires_object is not None:
                if focused_object is not None or focused_object.type != requires_object:
                    return self._reject(ClarifyReason.MISSING_FOCUSED_OBJECT)

        # 4,校验成功
        return TurnPlanValidationResult(valid=True)



