from pydantic import BaseModel


class FlowStepLink(BaseModel):
    """
    模板边（基类）
    """
    target: str # 下一步的stepid

class StaticLink(FlowStepLink):
    """
    静态边
    对应 next 的值是字符串
    """
    pass

class ConditionalLink(FlowStepLink):
    """
    对应的是 next:[{if:"xxxxxx", then:step_id}]
    step里面处理：then放在target， if 赋值给condition里面
    else:放在FallbackLink的target里面
    """
    condition: str  # 接收if 中的 xxxxxx

class FallbackLink(FlowStepLink):
    """
    对应的是 next:[{else:step_id}]
    """
    pass
