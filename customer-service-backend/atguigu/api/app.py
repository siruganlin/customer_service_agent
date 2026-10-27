from contextlib import asynccontextmanager

from fastapi import FastAPI

from atguigu.api.routers.chat_router import router
from atguigu.api.routers.denpndencies import init_dialogue_engine
from atguigu.infrastructure.database import init_db_engine, close_db_engine
from atguigu.infrastructure.http_client import init_http_client, close_http_client

"""
1,启动服务:uvicorn启动
2，执行数据库的初始化:引擎,数据库所管理的连接池，session工厂对象
3，遇到yield：暂停当前的 lifespan 函数执行，交出执行权给fastapi框架然后原地等待不会再继续执行了
4,此时fastapi正式启动，开始监听端口18082，接受客户端发送的api请求
5,当关闭服务器的时候，fastapi收到服务器的关闭信号，通知lifespan继续往下执行
6，程序从暂停的yield恢复
7,执行close_db_engine() 清理数据库资源，服务停止
"""


# fastapi应用的生命周期管理器
@asynccontextmanager
async  def lifespan(app: FastAPI):

    # app可以挂载一些信息
    print("服务启动")

    #app.state: 全局状态
    # app.state.abc = 'abc'

    # 初始化数据库连接资源
    init_db_engine()

    init_http_client()

    await init_dialogue_engine()
    yield # 开始接受fastapi的请求

    await close_db_engine()
    await close_http_client()
    print("服务停止")

# 挂载生命周期函数
app = FastAPI(description="电商小二",lifespan=lifespan)
app.include_router(router)

