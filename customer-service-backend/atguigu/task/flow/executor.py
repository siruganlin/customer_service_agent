from atguigu.domain.contexts import CollectedSystemContext
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import ActionResult
from atguigu.task.flow.flows import FlowsList
from atguigu.task.action.runner import ActionRunner, ActionCall
from atguigu.task.flow.links import StaticLink, ConditionalLink, FallbackLink
from atguigu.task.flow.steps import FlowStep, StartFlowStep, EndFlowStep, CollectFlowStep, ActionFlowStep


class FlowExecutor:
    """
    流程执行器：推进yaml中定义的业务任务流程以及系统任务流程
    """

    async def run_task(
            self,
            state: DialogueState,
            flows: FlowsList,
            action_runner: ActionRunner) -> list[BotMessage]:

        messages: list[BotMessage] = []
        # 外层循环
        while True:

            # 1 内层循环
            # 对流程做推进，判断每个步骤（step）的类型，当类型是action的时候从内层循环退出，在外层循环执行action
            action_call: ActionCall = self.advanced_until_action(state, flows)

            # 2 当action是action_listen的时候，用break结束本轮会话
            if action_call.action_name == "action_listen":
                break
            else:

                # 3. 执行action，更新槽位信息、组装message，然后进入下一轮循环
                action_result: ActionResult = await action_runner.run(action_call, state)
                state.set_slots(action_result.slot_updates)
                messages.extend(action_result.message)

        return messages

    def advanced_until_action(self, state: DialogueState, flows: FlowsList) -> ActionCall:

        while True:
            # 1. 获取当前任务
            current_active_task = state.current_active_task()

            # 2. 如果没有当前任务
            # 业务流程刚跑完end，active_task和active_system_task都是空
            # 刚启动会话，还没开始任何任务
            if current_active_task is None:
                return ActionCall(action_name = "action_listen")

            # 3. 如果有当前任务，则获取流程对象
            flow = flows.get_flow_by_id(current_active_task.flow_id)

            # 4. 获取当前步骤
            step = flow.get_step_by_id(current_active_task.step_id)

            # 5. 根据step组装ActionCall
            action_call: ActionCall = self._run_step(state, step, flows)

            # 6. 如果step的类型是action，则退出循环
            if action_call is not None:
                return action_call

    def _run_step(self, state: DialogueState, step: FlowStep, flows: FlowsList) -> ActionCall | None:

        if isinstance(step, StartFlowStep):
            return self._run_start_step(step, state)

        if isinstance(step, EndFlowStep):
            return self._run_end_step(state)

        if isinstance(step, CollectFlowStep): # action_response + action_listen
            return self._run_collect_step(step, state, flows)

        if isinstance(step, ActionFlowStep):
            return self._run_action_step(step, state)

        return None

    def _run_end_step(self, state: DialogueState)-> None:

        # 如果当前正在执行系统流程，并且已经到了最后一步，那么就结束系统流程
        if state.active_system_task:
            state.end_active_system_task()
        else:

            # 如果当前不是系统流程，那么就是业务流程，则结束业务流程
            state.end_active_task()

        # 清空后返回None，仅如内存循环的下一轮
        # 如果当前清空的是active_system_task，则内层循环的下一轮的 state.current_active_task() 会取出业务流程
        # 如果当前清空的是 active_task, 则内存循环
        return None

    def _run_start_step(self, step: StartFlowStep, state: DialogueState) -> None:

        # 1. 推进流程
        self._advanced_next_step(state, step)

        # 2. 返回None
        return None

    def _advanced_next_step(self, state: DialogueState, step: FlowStep):

        # 1. 寻找下一个step_id
        next_step_id = self._select_next_step(step, state)
        # 2. 修改流程的step_id
        state.current_active_task().step_id = next_step_id

    def _select_next_step(self, step: FlowStep, state: DialogueState) -> str:

        for link in step.next:
            if isinstance(link, StaticLink):
                return link.target
            if isinstance(link, ConditionalLink):
                #if eval("slots.get('product_id')"):
                if self._eval_condition(state, link.condition):
                    return link.target
            if isinstance(link, FallbackLink):
                return link.target

        return "没有下一步"

    def _eval_condition(self, state: DialogueState, condition: str):

        data = {
            "slots": state.active_task.slots,
            "context": state.current_active_task().model_dump(mode="json")
        }
        return bool(eval(condition, {"__builtins__": None}, data))

    def _run_action_step(self, step: ActionFlowStep, state: DialogueState) -> ActionCall:

        # 1. 推进流程
        self._advanced_next_step(state, step)

        # 2. 构造action_call
        action_call = self._build_action_call(state, step)

        # 3. 返回一个action_call
        return action_call

    def _build_action_call(self, state: DialogueState, step: ActionFlowStep) -> ActionCall:

        # 1. 获取action_name
        action_name = step.action
        action_kwargs = step.args

        # 如果是字符串
        if isinstance(action_kwargs, str):
            action_kwargs = state.active_system_task.model_dump(mode="json")[action_kwargs.split(".")[1]]

        return ActionCall(
            action_name=action_name,
            action_kwargs=action_kwargs
        )

    def _run_collect_step(self, step: CollectFlowStep, state: DialogueState, flows: FlowsList) -> None:

        # 1. 尝试自动补槽
        self._try_to_fill_collect_slot_object(state, step)

        # 2. 判断是否已经填上了
        if state.active_task.slots.get(step.slot_name):
            self._advanced_next_step(state, step)
            return None

        # 激活系统过场流程(问用户：例如 请告诉我你的订单号)
        state.start_active_system_task(CollectedSystemContext(
            step_id=flows.get_flow_by_id("system_collect_information").start_step().id,
            slot_name=step.slot_name,
            response=step.response.model_dump(mode="json")
        ))

        return None

    def _try_to_fill_collect_slot_object(self, state: DialogueState, step: CollectFlowStep):

        if state.focused_object is None:
            return

        if step.slot_name == "order_name" and state.focused_object.type == "order":
            state.set_slots({
                step.slot_name: state.focused_object.id
            })

        if step.slot_name == "product_id" and state.focused_object.type == "product":
            state.set_slots({
                step.slot_name: state.focused_object.id
            })








