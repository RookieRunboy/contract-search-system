# Change: 修复合同列表在笔记本屏幕上的排版问题

## Why
当前合同列表在笔记本等小屏幕设备上显示时，"合同名称"列被严重压缩，导致每行只能显示 2-3 个中文字符，形成垂直的文字排列，用户体验极差。根本原因是表格固定宽度列的总和 (~970px) 超出了可用屏幕宽度，而"合同名称"列使用 `width: undefined` 自适应分配剩余空间，导致空间不足。

## What Changes
- 为合同名称列设置最小宽度 `minWidth: 200`，确保有足够的显示空间
- 为 Table 组件添加 `scroll={{ x: 1200 }}` 配置，当屏幕宽度不足时启用水平滚动
- 适当压缩其他固定列的宽度，为合同名称腾出更多空间
- 优化表格在小屏幕上的响应式体验

## Impact
- Affected specs: `contract-management`
- Affected code: `frontend/src/pages/UploadPage.tsx`（表格列定义和 Table 组件配置）
