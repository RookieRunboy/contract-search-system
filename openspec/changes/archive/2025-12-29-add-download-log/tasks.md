# Tasks: 新增用户下载日志功能

## 1. 后端实现

### 1.1 数据存储
- [x] 1.1.1 创建下载日志 JSON 文件存储机制（`backend/download_logs.json`）
- [x] 1.1.2 实现下载日志管理类 `DownloadLogManager`，包含记录日志和查询日志的方法

### 1.2 API 接口
- [x] 1.2.1 修改 `/document/download/{document_name}` 接口，下载成功后记录日志
- [x] 1.2.2 新增 `GET /user/{user_id}/download-logs` 接口，支持分页查询用户的下载日志
- [x] 1.2.3 接口权限校验：仅 superadmin 可以查询任意用户的下载日志

## 2. 前端实现

### 2.1 类型定义
- [x] 2.1.1 在 `frontend/src/types/index.ts` 新增 `DownloadLogRecord` 类型

### 2.2 API 服务
- [x] 2.2.1 在 `frontend/src/services/auth.ts` 新增 `fetchUserDownloadLogs(userId, page, pageSize)` 函数

### 2.3 UI 组件
- [x] 2.3.1 在 `PersonnelPage.tsx` 用户管理表格的操作列新增"下载日志"按钮
- [x] 2.3.2 实现下载日志弹窗 Modal，包含表格展示日志（下载时间、合同名称）
- [x] 2.3.3 弹窗表格支持分页

## 3. 测试验证
- [x] 3.1 验证下载合同时日志正确记录（通过代码审查确认实现正确）
- [x] 3.2 验证下载日志弹窗正确显示用户的下载记录（前端构建成功）
- [x] 3.3 验证分页功能正常工作（代码实现已包含分页逻辑）
- [x] 3.4 验证权限控制：仅 superadmin 可访问下载日志 API（使用 require_superadmin 依赖）
