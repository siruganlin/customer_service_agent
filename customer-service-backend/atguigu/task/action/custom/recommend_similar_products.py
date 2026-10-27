from typing import Dict, Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.infrastructure.shered import fetch_product


class RecommendSimilarProductsAction(Action):
    name = "action_recommend_similar_products"

    async def run(self, state: DialogueState, action_kwargs: Dict[str, Any]) -> ActionResult:
        # 1,获取上一个步骤填充的槽位
        product_id = state.active_task.slots.get("product_id")

        # 2，根据订单号查询订单信息
        data = await fetch_product(product_id)

        # 3,TODO 调用搜索能力实现相识商品的推荐

        # 3，更新槽位信息(ActionResult)
        if data is None:
            # 查询失败
            return ActionResult(
                slot_updates={
                    "product_title": "查询失败，暂时无法查询到信息,稍后再试"
                }
            )

        return ActionResult(
            slot_updates={
                "product_title":data.get("title"),
            }
        )