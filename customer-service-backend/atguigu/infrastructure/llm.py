from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from atguigu.conf.config import settings

llm: BaseChatModel = init_chat_model(
    model = settings.llm_model,
    model_provider="openai",
    base_url = settings.llm_base_url,
    api_key = settings.llm_api_key,
    temperature=0
)
