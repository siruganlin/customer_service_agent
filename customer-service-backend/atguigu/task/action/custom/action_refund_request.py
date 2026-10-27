from typing import Dict, Any

from atguigu.domain.state import DialogueState
from atguigu.infrastructure.shered import submit_refund_request
from atguigu.task.action.base import Action, ActionResult


class RefundRequestAction(Action):

    name = "action_refund_request"

    async def run(self, state: DialogueState, action_kwargs: Dict[str, Any]) -> ActionResult:

        # 1,获取上一个步骤填充的槽位
        order_number = state.active_task.slots.get("order_number")
        refund_reason = state.active_task.slots.get("refund_reason")

        # 2，根据订单号查询订单信息
        data = await submit_refund_request(order_number)

        # 3，更新槽位信息(ActionResult)
        if data is None:
            # 查询失败
            return ActionResult(
                slot_updates={
                    "order_number": order_number,
                    "refund_reason": refund_reason
                }

            )

        return ActionResult()