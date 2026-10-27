from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import UserMessage, BotMessage
from atguigu.domain.state import Turn
from atguigu.infrastructure.llm import llm
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt


class ChitChatResponder:

    async def respond(self, user_message: UserMessage, recent_turn: list[Turn]):

        # 1,将用户消息转化为str
        user_message = HistoryBuilder.render_user_message(user_message)
        # 2,组装history
        history= HistoryBuilder.build(recent_turn)
        # 3,构建提示词模板
        prompt_text = load_prompt("chitchat_respond")
        prompt = PromptTemplate.from_template(template=prompt_text,template_format="jinja2")

        chain = prompt | llm | StrOutputParser()
        response = await chain.ainvoke({
            "history":history,
            "user_message":user_message
        })

        return [BotMessage(text = response)]