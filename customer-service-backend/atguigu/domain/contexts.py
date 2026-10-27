"""
对话上下文
"""
from typing import Literal, Annotated
from pydantic import BaseModel, Field, TypeAdapter


class TaskContext(BaseModel):
    """
    业务任务上下文
    """
    flow_id: str  # 业务任务的流程ID
    step_id: str | None = None  # 业务任务下的步骤ID
    slots: dict = {}  # 业务任务执行过程中收集到的槽位数据

class SystemContext(BaseModel):
    """
    系统流程上下文
    定义具体流程的通用属性
    """
    flow_id: str  # 系统流程的流程ID
    step_id: str | None = None  # 系统流程当前执行的步骤ID

class StartedSystemContext(SystemContext):
    """
    流程开始
    """
    started_flow_id: str = ""  #新开始的业务任务ID
    started_flow_name: str = ""  #新开始的业务任务名字
    # 使用Literal类型固定flow_id值，作为Discriminated Union（联合类型的区分字段）的区分字段 强约束flow_id字段
    flow_id: Literal["system_task_started"] = "system_task_started"

class InterruptedSystemContext(SystemContext):
    """
    流程中断
    interrupted:中断的,打断的
    """
    interrupted_flow_id: str = ""  # 被中断的旧业务任务ID
    interrupted_flow_name: str = ""  # 被中断的旧业务任务名字
    started_flow_id: str = ""  # 新开始的业务任务ID
    started_flow_name: str = ""  # 新开始的业务任务名字
    flow_id: Literal["system_task_interrupted"] = "system_task_interrupted"

class CanceledSystemContext(SystemContext):
    """
    流程取消
    """
    canceled_flow_id: str = ""  # 被取消的业务任务ID
    canceled_flow_name: str = ""  # 被取消的业务任务名字
    flow_id: Literal["system_task_canceled"] = "system_task_canceled"

class ResumedSystemContext(SystemContext):
    """
    流程恢复
    resumed:恢复
    """
    resumed_flow_id: str = ""  # 被恢复的业务任务ID
    resumed_flow_name: str = ""  # 被恢复的业务任务名字
    flow_id: Literal["system_task_resumed"] = "system_task_resumed"

class CollectedSystemContext(SystemContext):
    """
    系统流程收集槽位信息
    """
    slot_name: str = ""  # 收集的槽位名
    response: dict =    {}  # 例如: {"text":"请告诉我你的订单号"}
    flow_id: Literal["system_collect_information"] = "system_collect_information"

# 定义系统流程的联合类型
SystemContextUnion = Annotated[
    StartedSystemContext |
    InterruptedSystemContext |
    CanceledSystemContext |
    CollectedSystemContext,
    # 定义鉴别字段，使用flow_id 作为鉴别字段
    Field(discriminator="flow_id")  # 鉴别器：告诉pydantic 看 flow_id 字段来区分哪个是子段
]

# 定义一个适配器（用于反序列化）
system_context_adapter = TypeAdapter(SystemContextUnion)
