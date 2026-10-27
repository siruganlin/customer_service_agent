from atguigu.chitchat.responder import ChitChatResponder
from atguigu.domain.messages import UserMessage, BotMessage
from atguigu.domain.state import DialogueState


class ChitChatHandler:

    def __init__(self,responder: ChitChatResponder):
        self.responder = responder

    async def handle(self, state: DialogueState) -> list[BotMessage]:

        # 1,获取本轮会话的用户问题
        pending_turn = state.pending_turn
        user_message = pending_turn.user_message

        # 2,获取之前的会话轮次
        turns = state.current_session().turns

        # 3,调用respond方法获取结果
        return await self.responder.respond(
            user_message = user_message,
            recent_turn=turns

        )