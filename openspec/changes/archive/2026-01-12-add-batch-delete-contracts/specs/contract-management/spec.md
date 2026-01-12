# 合同管理 SPEC

## ADDED Requirements

### Requirement: 批量删除合同
The system SHALL provide a batch delete function to allow users to remove multiple contracts at once.

#### Scenario: 批量删除选中合同
- **GIVEN** 用户在合同列表页面
- **WHEN** 用户勾选多个合同（例如 "A.pdf" 和 "B.pdf"）
- **AND** 用户点击“批量删除”按钮
- **AND** 用户在确认弹窗中点击“确定”
- **THEN** 前端向后端发送批量删除请求
- **AND** 列表刷新，被选中的合同从列表中消失
- **AND** 系统提示删除成功信息
