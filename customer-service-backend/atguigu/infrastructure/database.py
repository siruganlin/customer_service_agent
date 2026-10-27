import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from atguigu.conf.config import settings

# 定义全局的异步session
# 定义全局的session工厂
engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None
"""
定义全局变量的作用就是为了其他函数可以拿到这个值
"""

# 初始化数据库连接资源
def init_db_engine():

    print("初始化数据库连接资源")

    global  engine, async_session

    # 先创建引擎：数据库资源管理器，管理着数据库连接池
    engine = create_async_engine(
        settings.database_url,
        echo = True, # 打印sql语句
        echo_pool = True, # 打印连接池相关的日志
        pool_size = 10,  # 数据库连接池常驻的连接数量
        max_overflow = 10, # pool_size满了之后可以扩展的数量，默认的最大扩展连接数量
        pool_recycle = 300, # 默认是-1叫做不会主动回收连接,300（五分钟）主动释放空闲连接：如果空闲连接五分钟没有人去连接他，这个连接就会被释放掉
        # 每次从数据库连接池取出取出链接之前,先向数据库发送一个心跳查询(select 1) 检查连接是否可用
        # 若链接已断开则自动丢弃当前链接并创建新连接，避免发生连接失效的错误
        pool_pre_ping=True,
    )
    """
    每一次连接数据库默认都会创建一个数据库连接池，结束之后会销毁这个连接
    高并发的场景下非常不友好，效率非常低
    加上pool_pre_ping=True这个参数后：
    会先创建一些数据库连接池，在请求连接的时候直接拿池里面现成的
    """

    # 再由引擎创建session
    # expire_on_commit=False TODO
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    """
    expire_on_commit:
    expire:过期
    commit：提交
    过期在提交之上，如果设置为True：commit之后就过期了，那么sandy.name查询语句就会自动执行一条sql（查询语句）从数据库中获取最新的值
        如果设置为false：commit不会过期，sandy.name查询不会获取数据库路的数据，而是会从sandy内存中获取
    注意:异步的场景不支持设置成Ture,所以异步场景必须设置成false
    """

# 关闭资源
async def close_db_engine():

    print("关闭数据库资源")

    if engine is not None:
        await engine.dispose()
