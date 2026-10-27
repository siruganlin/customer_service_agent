from typing import Dict, Any

from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.llm import llm
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.task.action.base import Action, ActionResult


class ActionResponse(Action):
    """生成AI和用户的返回信息"""
    name = "action_response"

    async def run(self, state: DialogueState, action_kwargs: Dict[str, Any]) -> ActionResult:

        # 获取mode:这个是action的返回值的生成方式，没有的话默认取static
        mode = action_kwargs.get("mode","static")

        if mode == "static":
            # 直接渲染回复
            text = action_kwargs["text"]
            rendered_text = self._render_text(text, state)
            return ActionResult(message=[BotMessage(text=rendered_text)])

        elif mode == "rephrase":
            # 1,渲染参考回复
            text = action_kwargs["text"]
            rendered_text = self._render_text(text, state)

            # 2,将参考回复进行重写
            prompt_text = action_kwargs["prompt"]
            message = await self._call_llm(prompt_text, state, rendered_text)

            # 3,组织结果
            return ActionResult(message=[BotMessage(text=message)])

        else: # mode == "generate":
            # 1,直接用模型生成答案
            prompt_text = action_kwargs["prompt"]
            message = await self._call_llm(prompt_text, state)

            # 2,组织结果
            return ActionResult(message=[BotMessage(text=message)])

        # return ActionResult()

    # 渲染text
    @staticmethod
    def _render_text(text: str, state: DialogueState) -> str:
        tp1 = Template(text)
        result = tp1.render(
            slots=state.active_task.slots if state.active_task else {},
            context = state.active_system_task or state.active_task # 判断在执行哪个方法就是看哪个里面取出来有值就用哪个（哪个方法有值就是在执行哪个步骤）
        )

        return result

    async def _call_llm(self, prompt_text: str, state: DialogueState, rendered_text: str = None) -> str:
        """使用llm对rendered_text进行重写"""
        # 1,初始化提示词模板
        prompt = PromptTemplate.from_template(prompt_text)
        # 2，构建执行链
        chain = prompt | llm | StrOutputParser()
        # 3，获取聊天历史记录
        history = HistoryBuilder.build(state.current_session().turns)
        #         # 4,获取user_message
        user_message = HistoryBuilder.render_user_message(state.pending_turn.user_message)
        bot_message = await chain.ainvoke({
            "history":history,
            "user_message":user_message,
            "current_response":rendered_text
        })
        return bot_message