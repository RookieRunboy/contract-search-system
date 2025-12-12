# Change: 新增用户下载日志功能

## Why
系统需要记录用户的合同下载行为，以便管理员能够追踪和审计用户的下载活动。当前系统缺乏对用户下载行为的监控能力，这对于合规审计和安全管理是一个重要缺失。

## What Changes
- **后端**：
  - 新增下载日志数据模型，记录用户ID、下载时间、合同文件名等信息
  - 修改现有的 `/document/download/{document_name}` 接口，在下载成功时记录日志
  - 新增 API 接口 `GET /user/{user_id}/download-logs` 获取指定用户的下载日志
- **前端**：
  - 在人员管理页面的用户管理列表的"操作"列新增"下载日志"按钮
  - 新增下载日志弹窗组件，展示该用户的下载记录（包含下载时间、合同名称）
  - 弹窗支持分页展示日志

## Impact
- Affected specs: `download-log`（新增）
- Affected code:
  - `backend/contractApi.py` - 修改下载接口，新增日志记录和查询接口
  - `frontend/src/pages/PersonnelPage.tsx` - 新增下载日志按钮和弹窗
  - `frontend/src/services/auth.ts` - 新增获取下载日志的 API 调用
  - `frontend/src/types/index.ts` - 新增下载日志类型定义
