# 规格说明: 招标文件/需求文本 AI 解析

## ADDED Requirements

### Requirement: 文本分析 API
系统 MUST 提供一个 API 接口，接受用户输入的文本字符串，并返回分析后的关键词和筛选条件。

#### Scenario: 成功解析需求文本
Given 系统后端服务正常运行且 LLM 服务可用
When 客户端发送 POST 请求到 `/api/bid-analysis/parse`，包含一段关于"某银行核心系统由于信创改造需要采购..."的文本
Then 系统应返回 HTTP 200
And 响应体应包含 JSON 数据
And JSON 数据中 `keywords` 字段应包含 ["银行", "核心系统", "信创"] 等相关词汇

#### Scenario: 空文本处理
Given 用户未输入任何内容
When 客户端发送空文本请求
Then 系统应返回 HTTP 400 错误，提示文本不能为空

### Requirement: 搜索页集成
系统前端 SHALL 在文档搜索页面（SearchPage）集成 AI 解析功能，通过 **侧边抽屉 (Drawer)** 形式交互，提供沉浸式的分析体验。

#### Scenario: 通过 AI 助手侧边栏填充搜索条件
Given 用户在文档搜索页面
When 用户点击搜索框内的 "✨" 智能助手图标
Then 系统从右侧滑出 "智能助手" 侧边栏
When 用户在侧边栏文本域中粘贴文本并点击 "智能分析"
Then 系统展示加载动画，并随后通过流式效果展示提取出的关键词和筛选条件
When 用户确认无误并点击 "执行搜索"
Then 侧边栏自动收起
And 搜索页面的搜索框内容无缝更新为提取的关键词
And 搜索页面的高级筛选栏根据提取结果自动填充
And 系统自动触发搜索并展示结果
