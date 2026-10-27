from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.chitchat.responder import ChitChatResponder
from atguigu.clarify.responder import ClarifyResponder
from atguigu.engine.builder import build_dialogue_engine
from atguigu.engine.dialogue_engine import DialogueEngine
# 必须通过这种方式引入database，需要的时候再获取 database.async_session()
from atguigu.infrastructure import database
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.provider import RAGProvider, FAQProvider, OderAPIProvider, ProductAPIProvider
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponder
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.plan.turn_vilidator import TurnPlanValidator
# 不要通过这种方式引入async_session，会是一个NoneType
# from atguigu.infrastructure.database import async_session
from atguigu.repository.diologue_state_repository import DialogueStateRepository
from atguigu.service.dialogue_service import DialogueService
from atguigu.task.action.builder import build_action_runner
from atguigu.task.action.runner import ActionRunner
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.loader import FlowLoader
from atguigu.task.handler import TaskHandler

"""
1，请求从前端交给fastapi fastapi作为web层他是调用service层
2,service层调用repository层
3，repository层初始化的时候通过get_session()方法将self.session进行依赖注入
4,执行async with async_session() as session:(会先初始化一个连接池（池子中放若干session）)
5，从数据库连接池中取出一个session对象:yield session
6,yield 使当前 get_session() 停止执行,把session对象向外提供:交给repository使用
7,一直到此次调用中相关的repository,service,web全部逻辑执行完成，返回响应之后,程序会回到yield的下方
8,退出async with,session关闭归还给数据库连接池

总结：yield之前 = 创建资源的阶段,yield向外层交付资源。请求处理完成之后，执行yield上下文的资源清理工作,释放资源 
"""

_dialogue_engine: DialogueEngine | None = None

async def init_dialogue_engine():
    global _dialogue_engine
    _dialogue_engine = await build_dialogue_engine()  # 构建引擎的方法

async def get_engine():
    return _dialogue_engine

# 创建session实例
async def get_session():
    # 异步方式获取session对象
    async with database.async_session() as session:


        # yield将session返回,使程序停留在此位置，直到外层调用
        yield session

# 创建 repository的实例
async def get_dialogue_state_repository(session: AsyncSession = Depends(get_session)):


    return DialogueStateRepository(session)

# 创建engine实例

# 创建service实例
async def get_dialogue_service(
        dialogue_state_repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        dialogue_engine: DialogueEngine = Depends(get_engine)
        ):

    return DialogueService(
        dialogue_state_repository=dialogue_state_repository,
        dialogue_engine=dialogue_engine
    )
