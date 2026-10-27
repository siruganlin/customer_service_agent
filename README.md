# 电商智能客服 Agent（customer_service_agent）

面向电商场景的 **LLM 对话客服系统**。核心是一套基于 FastAPI + LangGraph 的**对话流程引擎**，把"一次对话"建模成状态机而非单次 Prompt，实现意图识别、槽位填充、条件分支与工具调用。

> 本项目在尚硅谷课程项目基础上二次开发，重构了流程引擎与 Prompt 组装链路。

---

## 模块构成

| 模块 | 技术栈 | 作用 |
|---|---|---|
| `customer-service-backend/` | FastAPI · LangGraph · Pydantic | **对话流程引擎**：流程编排、槽位管理、条件跳转、Prompt 组装、会话历史 |
| `customer-service-frontend/` | Vue 3 · Vite | 控制台前端，用于对话与调试 |
| `ecommerce-service-backend/` | FastAPI | 模拟业务接口（订单 / 用户 / 商品），供 Agent 的 Action 调用 |

---

## 核心设计

对话不是一次 Prompt 调用，而是**有状态的多轮流程**：

- **Flow** —— 一段对话由若干 Step 组成，定义在 `flow_config/` 的 YAML 里，支持热加载
- **Step / Action** —— 每个 Step 执行一个动作：调业务接口、追问槽位、转人工
- **Link** —— 三种跳转方式
  - `StaticLink`：无条件跳到目标 Step
  - `ConditionalLink`：条件成立才跳转
  - `FallbackLink`：兜底分支
- **Slot** —— 跨轮次累积的结构化记忆（订单号、商品 ID、用户意图…）
- **HistoryBuilder** —— 把历史轮次折叠成紧凑的 Prompt 上下文，控制 token 开销

```
用户输入
   │
   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 意图识别      │──►│ 选择下一个   │──►│ 执行 Action  │
│ + 槽位填充    │   │ Step (Link) │   │ （工具调用）  │
└──────────────┘   └──────────────┘   └──────┬───────┘
   ▲                                         │
   └──────────── 会话状态回写 ◄───────────────┘
```

---

## 快速开始

### 后端（对话引擎）

```bash
cd customer-service-backend

cp .env.example .env      # 填入自己的配置
uv sync

uv run python -m atguigu.main
```

### 业务支撑服务

```bash
cd ecommerce-service-backend
cp .env.example .env
uv sync
uv run python main.py
```

### 前端

```bash
cd customer-service-frontend
npm install
npm run dev
```

---

## 配置

各后端模块复制 `.env.example` 为 `.env`，填写：

```ini
# LLM
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus-latest

# 服务
APP_HOST=127.0.0.1
APP_PORT=18082

# 业务支撑服务（18081）
COMMERCE_API_BASE_URL=http://127.0.0.1:18081/

# 数据库
DATABASE_URL=mysql+asyncmy://user:pass@127.0.0.1:3306/customer_service_ai0525?charset=utf8mb4
DATABASE_URL_SYNC=mysql+pymysql://user:pass@127.0.0.1:3306/customer_service_ai0525
```

以上为对话引擎配置；业务支撑服务使用其自身的 `.env.example`，端口为 `18081`。请提前创建各自配置的 MySQL 数据库和所需业务表。

> `.env` 已加入忽略规则；曾经提交过的凭据仍可能存在于旧 Git 历史中，首次公开请使用清理后的文件重新建仓。

---

## 目录结构

```
customer_service_agent/
├── customer-service-backend/
│   ├── atguigu/
│   │   ├── domain/            # 消息 / 上下文 / 状态模型
│   │   ├── engine/            # 对话引擎构建
│   │   ├── infrastructure/    # LLM、数据库、HTTP 客户端
│   │   ├── prompts/           # Prompt 模板 + 历史构建
│   │   ├── task/              # flow / step / action / link 实现
│   │   ├── plan/              # 规划相关模型
│   │   └── main.py            # 服务入口
│   ├── flow_config/           # 流程 YAML 定义
│   └── pyproject.toml
├── customer-service-frontend/ # Vue 3 + Vite
└── ecommerce-service-backend/ # 业务支撑接口
```

---

## 设计要点

- **业务可替换**：所有外部调用收在 `Action` 抽象后面，换业务系统不用改引擎
- **流程可配置**：对话流程写在 YAML 里，运营侧可直接调整分支
- **上下文可控**：`HistoryBuilder` 按窗口 + 摘要压缩历史，避免长对话 token 爆炸

---

## License

[MIT](LICENSE)
