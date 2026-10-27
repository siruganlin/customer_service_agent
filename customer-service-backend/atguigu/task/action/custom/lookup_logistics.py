from typing import Dict, Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.infrastructure.shered import fetch_logistics


class LookupLogisticsAction(Action):
    name = "action_lookup_logistics"

    async def run(self, state: DialogueState, action_kwargs: Dict[str, Any]) -> ActionResult:

        # 1,获取上一个步骤填充的槽位
        order_number = state.active_task.slots.get("order_number")

        # 2，根据订单号查询订单信息
        data = await fetch_logistics(order_number)

        # 3，更新槽位信息(ActionResult)
        if data is None:
            # 查询失败
            return ActionResult(
                slot_updates={
                    "logistics_company": "未知",
                    "tracking_number": "未知",
                    "logistics_status": "暂时无法查询当前进度"
                }
            )
        return ActionResult(slot_updates={
            "tracking_number": data.get("tracking_number"),
            "logistics_company": data.get("logistics_company"),
            "logistics_status": data.get("status_desc") or data.get("status"),
        })