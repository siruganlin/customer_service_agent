import json
from typing import Dict, Any

from atguigu.api.schema import HistoryMessage, ChatObject
from atguigu.domain.state import Turn
from atguigu.domain.messages import UserMessage, BotMessage, FocusedObject, MessageType

class HistoryBuilder:
    @staticmethod
    def build( turns: list[Turn]) -> str:
        """
        将多轮对话的列表转化成字符串的形式
        :param turns:
        :return:
        """
        msgs: list[str] = []
        for turn in turns:
            # 1，处理用户消息
            user_message = turn.user_message
            user_message_str = HistoryBuilder._render_user_message(user_message)
            msgs.append(f"USER: {user_message_str}")
            # 2,处理机器人消息
            for bot_msg in turn.bot_messages:
                bot_msg_str = HistoryBuilder._render_bot_message(bot_msg)
                msgs.append(f"BOT: {bot_msg_str}")

        return "\n".join(msgs)

    @staticmethod
    def _render_user_message(user_message: UserMessage):

        if user_message.type is MessageType.TEXT:
            return HistoryBuilder._render_text_msg(user_message.text)
        else:
            return HistoryBuilder._rander_obj_msg(user_message.object)

    @staticmethod
    def render_user_message(user_message: UserMessage):
        return HistoryBuilder._render_user_message(user_message)

    @staticmethod
    def _render_bot_message(bot_msg: BotMessage):

        if bot_msg.text:
            return HistoryBuilder._render_text_msg(bot_msg.text)
        else:
            return HistoryBuilder._render_obj_msg(bot_msg.object)

    @staticmethod
    def _render_text_msg(text):
        return text.strip()

    @staticmethod
    def _rander_obj_msg(object_msg: FocusedObject):
        label = "订单对象" if object_msg.type == "order" else "商品对象"
        id = object_msg.id
        title = object_msg.title
        attributes: Dict[str, Any] = object_msg.attributes
        # attributes_str = "，".join([f"{key}：{value}" for key, value in attributes.items()])
        # 字典转字符串
        attributes_str = json.dumps(attributes, ensure_ascii=False)
        return f"[{label}={label}, id={id}, title={title}, attributes={attributes_str}]"

    @staticmethod
    def get_user_message(session_id: str, user_message: UserMessage) -> HistoryMessage:

        user_obj = ChatObject(**user_message.object.model_dump()) if user_message.object else None
        return HistoryMessage(
            session_id=session_id,
            role="user",
            text=user_message.text,
            object=user_obj
        )

    @staticmethod
    def get_bot_message(session_id: str, bot_message: BotMessage) -> HistoryMessage:

        bot_obj = ChatObject(**bot_message.object.model_dump()) if bot_message.object else None
        return HistoryMessage(
            session_id=session_id,
            role="bot",
            text=bot_message.text,
            object=bot_obj
        )
