# AI 文本解析功能设计

## 架构概览

本功能旨在连接用户输入的非结构化文本与系统的结构化搜索能力。

### 核心流程
1.  **入口**: 在 `SearchPage` 的搜索框内右侧，放置一个 **"✨ AI 助手"** 图标/按钮。
2.  **唤起**: 点击图标，从屏幕右侧滑出 **"智能助手侧边栏" (AI Copilot Drawer)**。即使侧边栏打开，用户仍可看到左侧的搜索结果列表。
3.  **输入**: 侧边栏内提供一个大尺寸的、带有玻璃拟态 (Glassmorphism) 效果的文本输入区域，提示"请粘贴招标文件或需求描述..."。
4.  **沉浸式分析**: 
    - 用户点击"智能分析"。
    - 侧边栏展示"AI 思考中"的动态波纹动画 (Ripple/Wave Animation)。
    - 分析结果不是一次性出现，而是通过**流式打字机效果** (Streaming Effect) 逐个显示关键词和筛选条件。
5.  **交互式确认**:
    - **关键词**: 以悬浮气泡 (Floating Chips) 形式展示。用户点击气泡可将其"剔除"。
    - **筛选条件**: 以卡片形式展开。
6.  **一键应用 (Magic Apply)**: 
    - 用户点击 "✨ 执行搜索"。
    - 侧边栏自动收起。
    - **动画效果**: 关键词气泡仿佛"飞入"主搜索框；筛选条件自动填入并高亮。
    - 页面自动刷新搜索结果。

## 数据结构 (Interface)

```typescript
interface AnalysisResult {
    keywords: string[]; // 提取的搜索关键词，用于全文检索
    filters: ContractFilters; // 提取的结构化筛选条件
}

interface ContractFilters {
    customer_name?: string; // 客户名称
    our_entity?: string; // 我方签约主体
    contract_type?: string; // 合同类型/方向 (对应分类)
    min_amount?: number; // 最小金额暗示
    max_amount?: number; // 最大金额暗示
    date_range_start?: string; // 时间范围开始 (YYYY-MM-DD)
    date_range_end?: string; // 时间范围结束 (YYYY-MM-DD)
    customer_category_level1?: string; // 客户一级分类
    customer_category_level2?: string; // 客户二级分类
}
```

## Prompt 设计思路

Prompt 需要指导 LLM 完成两个任务：
1.  **关键词提取**: 从文本中识别核心技术栈、业务领域、特定产品名，作为搜索关键词。
2.  **条件映射**: 识别文本中隐含的硬性约束，如"要求过往案例金额不低于500万" -> `min_amount: 5000000`。

### 示例 Prompt Template

```text
你是一个专业的合同招投标分析专家。请分析以下用户输入的文本（可能是招标文件摘要或需求描述），并提取用于在合同库中检索相似案例的关键信息。

请提取以下两类信息，并以 JSON 格式返回：
1. keywords: 提取 3-5 个最核心的搜索关键词（技术栈、核心业务），不要太泛。
2. filters: 尝试提取隐含的筛选条件，包括：
   - customer_category_level1: 客户一级分类（如银行、保险、证券、政府、企业等）
   - min_amount: 最低金额要求（数字，单位元）
   - date_range_start: 如果有明确的时间要求（如"近三年"），该字段为开始日期 (YYYY-MM-DD)
   - our_entity: 如果指定了必须是某个主体

文本内容：
{{text}}

返回 JSON 格式：
{
  "keywords": ["...", "..."],
  "filters": {
    "min_amount": null,
    "customer_category_level1": null,
    ...
  }
}
```
