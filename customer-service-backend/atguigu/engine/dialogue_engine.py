from typing import List

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.clarify.responder import ClarifyResponder
from atguigu.domain.messages import UserMessage, ProcessResult, MessageType
from atguigu.domain.state import DialogueState
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.plan.models import TurnPlan, ClarifyReason
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.plan.turn_vilidator import TurnPlanValidator
from atguigu.task.command.models import Command, SetSlotsCommand
from atguigu.task.flow.flows import FlowsList
from atguigu.task.flow.steps import CollectFlowStep
from atguigu.task.handler import TaskHandler
import time
"""
处理用户的问题
"""
class DialogueEngine:

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowledgeHandler,
            chitchat_handler: ChitChatHandler,
            clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator

    async def process_message(self,dialogue_state: DialogueState, user_message: UserMessage) -> ProcessResult:

        # 根据user_message的内容，调用LLM进行路由,判断需要执行哪条轨道(业务流程，RAG检索，闲聊) 然后执行某一条轨道
        # 1,准备会话（如果没有则创建，如果有则获取）
        self._prepare_session(dialogue_state)
        # 2,开启本轮会话（创建turn对象）
        self._bengin_turn(dialogue_state,user_message)

        # 3,判断消息的类型
        # 3.1,if 处理文本消息 获取AI客服的回复
        if user_message.type is MessageType.TEXT:
            messages = await self._handler_text_message(dialogue_state)
        else:
            # 3.2,else 处理对象消息
            # 调用:set_focused_object设置当前聚焦对象
            dialogue_state.set_focused_object(user_message.object)
            messages = await self._handler_object_message(user_message, dialogue_state)

        # 4,提交本轮记录
        # 4.1将AI回复的消息写入在pending_turn中
        dialogue_state.pending_turn.bot_messages.extend(messages)

        # 4.2,将本轮的pending_turn消息提交到session (将Turn存储在Session的Turns列表中)

        dialogue_state.commit_pending_turn()
        # 5,组装结果并返回
        return ProcessResult(
            sender_id=dialogue_state.sender_id,
            message_id=user_message.message_id,
            messages=messages
            )

    def _prepare_session(self, dialogue_state: DialogueState) -> None:
        """
        获取或初始化session会话
        :param dialogue_state:
        :return:
        """
        # 1，获取当前的会话
        current_session = dialogue_state.current_session()
        # 2,如果没有则：创建一个session
        if current_session is None:
            dialogue_state.start_session()
            return

        # 3,判断会话是否过期
        now = time.time()
        if now - current_session.last_activity_at > 60 * 60 * 1: # 一个小时
            # 关闭会话
            dialogue_state.close_current_session()

            # 重置dialogue_state的运行状态
            dialogue_state.reset_runtime_state_for_new_session()

            # 开启一个新的会话
            dialogue_state.start_session()
        else:
            # 更新会话（会话续期）
            current_session.last_activity_at = now

    def _bengin_turn(self, dialogue_state, user_message):
        """
        开始一个Turn
        :param dialogue_state:
        :param user_message:
        :return:
        """
        dialogue_state.begin_turn(user_message)

    async def _handler_text_message(self, dialogue_state: DialogueState):

        # 使用TurnPlanner理解用户意图(LLM)，并生成本轮的计划
        turn_plan: TurnPlan = await self.turn_planner.predict(dialogue_state,self.task_handler.flows,
                                                              self.knowledge_handler.knowledge_intents)

        # 使用TurnPlanValidator 来处理是否有模型幻觉 和 用户不规范的提问
        validated = self.turn_plan_validator.validate(
                turn_plan,
                self.task_handler.flows,
                dialogue_state,
                self.knowledge_handler.knowledge_intents)

        # 判断validated的校验结果
        if not validated.valid:
            return await self.clarify_responder.respond(dialogue_state, validated.reason)

        # 根据意图识别的结果执行对应的业务逻辑或者对无效意图做澄清处理
        if turn_plan.task is not None:
            return await self.task_handler.handle(
                commands = turn_plan.task.commands,
                state = dialogue_state
            )

        elif turn_plan.knowledge is not None:
        # KnowledgeHandler
            return await self.knowledge_handler.handle(intents=turn_plan.knowledge.intents,state=dialogue_state)

        else:
            return await self.chitchat_handler.handle(state=dialogue_state)

    async def _handler_object_message(self, message: UserMessage, state: DialogueState):

        # 1,将对象消息解析为command（SetlSotsCommand）
        commands = self._resolve_object_commands(
            message=message,
            state=state,
            flows=self.task_handler.flows,
        )
        # 2,判断commands命令是否已经存在(流程的步骤刚好需要你点击卡片)
        # 场景A 有流程 有槽位
        if commands:
            return await self.task_handler.handle(commands=commands, state = state)

        # 场景C 有流程 没有槽位
        if state.active_task is not None:
            # 传递空命令,让流程按原来的节奏继续
            return await self.task_handler.handle(commands=[], state = state)

        # 场景B:没有流程 澄清
        return await self.clarify_responder.respond(
            state = state,
            reason=ClarifyReason.OBJECT_REQUIRES_INTENT
    )

    def _resolve_object_commands(self, message: UserMessage, state: DialogueState, flows: FlowsList) -> List[Command]:
        """
        生成添槽命令
        :param message:
        :param state:
        :param flows:
        :return:
        """
        # 1，获取聚焦对象
        focused_object = message.object
        if focused_object is None:
            return []

        # 2，获取聚焦对象的类型
        object_type = focused_object.type

        # 3,判断对象类型
        # 3.1 order
        if object_type == "order":
            # 判断能否添槽
            if self._flow_has_unfilled_collect_slot(state, flows, "order_number"):
                # 生成添槽命令
                return [SetSlotsCommand(command="set_slots",slots={"pro": focused_object.id})]

            return []
        # 3.2 product
        if object_type == "product":
            if self._flow_has_unfilled_collect_slot(state, flows, "product_id"):
                #3.2.1 生成添槽命令
                return [SetSlotsCommand(command="set_slots", slots={"product_id": focused_object.id})]

            return []

        return []

    def _flow_has_unfilled_collect_slot(self, state: DialogueState, flows: FlowsList, slot_name: str) -> bool:
        """
        判断当前情况下能否添槽
        :param state:
        :param flows:
        :param slot_name:
        :return:
        """
        # 1,获取活跃任务
        active_task = state.active_task
        if active_task is None:
            # 不存在活跃任务,不添槽
            return False

        # 2,根据活跃任务的id 获取当前流程
        flow_id = active_task.flow_id
        flow = flows.get_flow_by_id(flow_id)
        if flow is None:
            # 不存在流程 不添
            return False

        # 3，判断流程中的当前的槽位是否已经被填充过
        if active_task.slots.get(slot_name):
            # 槽位已经添过了
            return False

        # 4，遍历流程的每一步 查找是否存在收集该槽位的步骤
        for step in flow.steps:
            if isinstance(step, CollectFlowStep) and step.slot_name == slot_name:
                # 添槽
                return True
        # 步骤中不存在当前槽位,不填槽
        return False