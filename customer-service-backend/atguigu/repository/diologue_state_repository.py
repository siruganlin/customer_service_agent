import json
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from atguigu.domain.state import DialogueState
from atguigu.models.dialogue_state import DialogueStateRecord


class DialogueStateRepository:
    # session:会话的session对象,依赖注入进来
    def __init__(self, session: AsyncSession):
        self.session = session

    # 查找
    async def load_state(self, sender_id: str) -> DialogueState:

        # 1,定义sql
        sql = select(DialogueStateRecord).where(DialogueStateRecord.sender_id == sender_id)
        # 2，执行sql
        result = await self.session.execute(sql)
        # 3,获取结果(获取一条)
        state = result.scalar_one_or_none()

        # 4，如果数据库中有则获取
        if state:
            # 对局类型的转化json(str) -> Dict -> python类对象（DialogueState）
            json_dict = json.loads(state.state_json)
            return DialogueState.model_validate(json_dict)

        # 5，如果数据库中没有则创建
        return DialogueState(sender_id=sender_id)

    # 保存
    async def save_state(self, dialogue_state: DialogueState):

        # 1,将对象转成字典
        dict = dialogue_state.model_dump(mode="json")

        # 2,将字典转化为json str
        state_json = json.dumps(dict)

        # 方案一：if判断
        # 先执行一个查询语句 如果数据库中已经有sender_id 则执行更新语句 如果数据库中没有 则执行插入语句

        # 方案二:使用on_duplicate_key_update将insert升级为update
        # 向 dialogue_states 数据库表中插入一条记录
        insert_sql = insert(DialogueStateRecord).values(
            sender_id=dialogue_state.sender_id,
            state_json=state_json
        )

        # 如果数据库中已经有这个sender_id：因为sender_id是唯一的不能重复的所以上面的insert语句会失败 此时会自动升级为update更新语句
        # 3,前面的insert如果插入失败，则sql自动升级为update语句
        update_sql = insert_sql.on_duplicate_key_update(
            state_json=insert_sql.inserted.state_json
        )
        # 4,重新执行执行sql
        await self.session.execute(update_sql)
        # 5,提交事务
        await self.session.commit()
