from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.knowledge.provider import KnowledgeChunk
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponder


class KnowledgeHandler:
    def __init__(self,
                 knowledge_intents: dict[str, KnowledgeIntent],
                 provider_registry: KnowledgeProviderRegistry,
                 knowledge_responder: KnowledgeResponder):

        self.knowledge_intents = knowledge_intents
        self.provider_registry = provider_registry
        self.knowledge_responder = knowledge_responder

    async def handle(self, intents: list[str], state: DialogueState) -> list[BotMessage]:
        """
        处理用户意图
        :return:
        """
        chunks: list[KnowledgeChunk] = []
        provider_ids = self._get_provider_ids_by_intents(intents)
        for provider_id in provider_ids:
            provider = self.provider_registry.get(provider_id)
            current_chunks = await provider.retrieve(state)
            chunks.extend(current_chunks)

        return await self.knowledge_responder.respond(
            user_message=state.pending_turn.user_message,
            chunks=chunks,
            recent_turns=state.current_session().turns
        )

    def _get_provider_ids_by_intents(self, intents: list[str]):

        provider_ids: list[str] = []
        for intent in intents: # 为什么用extend：因为取出来的provider_ids中可能有多个数据
            provider_ids.extend(self.knowledge_intents[intent].provider_ids)

        return list(set(provider_ids))