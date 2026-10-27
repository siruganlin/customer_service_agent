from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import UserMessage, BotMessage
from atguigu.domain.state import Turn
from atguigu.infrastructure.llm import llm
from atguigu.knowledge.provider import KnowledgeChunk
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt


class KnowledgeResponder:

    async def respond(
            self,
            user_message:UserMessage,
            recent_turns: list[Turn],
            chunks: list[KnowledgeChunk]
                      ) -> list[BotMessage]:
        # 1，准备提示词模板需要的元素 render_user_message：将传进去的参数转化成字符串
        user_msg = HistoryBuilder.render_user_message(user_message)
        history = HistoryBuilder.build(recent_turns)
        content = "\n\n".join([chunk.content for chunk in chunks])
        # 2,加载提示词模板
        prompt_text = load_prompt("knowledge_respond")
        prompt_template = PromptTemplate.from_template(template=prompt_text,template_format="jinja2")
        # 3，创建调用链
        chain = prompt_template | llm | StrOutputParser()
        # 4，调用
        response =  await chain.ainvoke({
            "knowledge_content": content,
            "history": history,
            "user_message":user_msg,
        })
        # 5，返回结果
        return [BotMessage(text=response)]