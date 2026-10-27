import json
from typing import Any, Dict
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.llm import llm
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.plan.models import TurnPlan
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt
from atguigu.task.flow.flows import FlowsList


class TurnPlanner:
    """
    意图分析器
    作用: 根据自然语言 调用LLM 分析轨道类型
    """

    async def predict(self, dialogue_state, flow_list, intends:Dict[str,KnowledgeIntent]) -> TurnPlan:

       # 1,构建提示词模板中的占位内容（七部分）   TODO  使用 jinja2 模板引擎
        inputs_prompt = self._build_prompt_inputs(dialogue_state, flow_list,intends)

       # 2,调用大模型确定用户意图 将结果转化为python对象
        turn_plan: TurnPlan = await self._predict_from_inputs(inputs_prompt) # 反序列化
       
        return turn_plan

    def _build_prompt_inputs(self, dialogue_state: DialogueState, flow_list: FlowsList,intends):

        # 1，用户问题
        user_msg = HistoryBuilder._render_user_message(dialogue_state.pending_turn.user_message)
        # 2，对话历史
        current_conversation  = HistoryBuilder.build(dialogue_state.current_session().turns[-10: ])
        # 3,当前活跃任务
        active_task_json = json.dumps(
            dialogue_state.active_task.model_dump(mode="json"), ensure_ascii=False
                ) if dialogue_state.active_task is not None else None
        # 4,被挂起任务列表
        interrupted_tasks_json = json.dumps([paused_task.model_dump(mode="json")
                            for paused_task in dialogue_state.paused_tasks ],
                               ensure_ascii=False
                       )
        # 5,聚焦对象
        focused_object_json = json.dumps(
                        dialogue_state.focused_object.model_dump(mode="json"), ensure_ascii=False
                    ) if dialogue_state.focused_object is not None else None

        # 6,流程清单
        flow_dict = {
            "flows":[{k: v for k, v in flow.model_dump(mode="json").items() if k != "steps"} for flow in flow_list.flows]
        }
        available_flows_json = json.dumps(flow_dict , ensure_ascii=False)

        # 7，知识意图清单
        intends_dict = {"intends":[{"id":intend.id,"description":intend.description} for intend in intends.values()]}
        knowledge_intents_json = json.dumps(
            intends_dict
        ,ensure_ascii=False
        )

        return {
            "user_message": user_msg,
            "current_conversation": current_conversation,
            "active_task_json": active_task_json,
            "interrupted_tasks_json": interrupted_tasks_json,
            "focused_object_json": focused_object_json,
            "available_flows_json": available_flows_json,
            "knowledge_intents_json": knowledge_intents_json
        }

    async def _predict_from_inputs(self, inputs_prompt: dict[str,Any]) -> TurnPlan:

        prompt_template_str = load_prompt("turn_plan")
        prompt_template = PromptTemplate.from_template(template=prompt_template_str,template_format="jinja2")

        # 构建langchain的链式调用
        chain = prompt_template | llm | JsonOutputParser() # 将达模型生成的json字符串转化为dict

        llm_response_dict: dict[str,Any] = await chain.ainvoke(inputs_prompt)

        return TurnPlan.from_dict(llm_response_dict)