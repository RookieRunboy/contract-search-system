# Tasks: AI 文本解析功能

## Backend Tasks
- [ ] 在 `backend/llm_metadata_extractor.py` 中添加 `analyze_requirement` 方法 <!-- id: 0 -->
    - 设计新的 prompt template 用于提取关键词和筛选条件
    - 复用 `_call_llm_api` 和 `_parse_json_response`
    - 返回包含 `keywords` 和 `filters` 的字典
- [ ] 在 `backend/contractApi.py` 中新增 endpoint `POST /bid-analysis/parse` <!-- id: 1 -->
    - 接收 Request Body: `{"text": "..."}`
    - 调用 `metadata_extractor.analyze_requirement`
    - 处理异常并返回结果

## Frontend Tasks
- [ ] 创建新组件 `frontend/src/components/BidAnalysisDrawer.tsx` <!-- id: 2 -->
    - 使用 Ant Design `Drawer` 组件，设置 placement="right"
    - **Input View**: 包含大尺寸文本域，添加 Placeholder 提示
    - **Loading View**: 实现波纹或 Skeleton 加载动画
    - **Result View**: 
        - 使用 Tag Group 展示 Keywords (支持关闭标签)
        - 使用 Card 展示 Filters (Amount, Date, etc.)
    - 实现 "Apply" 按钮的交互逻辑
- [ ] 在 `frontend/src/pages/SearchPage.tsx` 中集成 `BidAnalysisDrawer` <!-- id: 3 -->
    - 在 Ant Design `Input.Search` 的 `suffix` 或 `enterButton` 旁自定义渲染一个 "✨" 图标按钮
    - 点击图标设置 `drawerVisible` 为 true
    - 实现 `handleAIAnalysisConfirm` 回调：
        - 接收分析结果
        - **增加过渡动画逻辑** (可选): 简单的状态更新即可，若有余力可做视觉飞入效果
        - 更新 `searchQuery` 和 `filters` state
        - 自动调用 `handleSearch`
- [ ] 优化 UI 细节 <!-- id: 4 -->
    - 确保侧边栏打开时，背景有适当的遮罩或模糊效果
    - 调整移动端适配（在小屏幕上 Drawer 可以全屏）
