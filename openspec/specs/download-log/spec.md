# download-log Specification

## Purpose
TBD - created by archiving change add-download-log. Update Purpose after archive.
## Requirements
### Requirement: Download Log Recording
系统 SHALL 在用户成功下载合同文档时自动记录下载日志。

日志记录 SHALL 包含以下信息：
- 日志ID（唯一标识）
- 用户ID（下载者）
- 合同文件名
- 下载时间（ISO 8601 格式）

#### Scenario: 用户下载合同成功时记录日志
- **WHEN** 用户通过 `/document/download/{document_name}` 接口成功下载合同
- **THEN** 系统自动创建一条下载日志记录，包含用户ID、合同文件名和当前时间

#### Scenario: 下载失败不记录日志
- **WHEN** 用户请求下载的合同文件不存在或下载过程发生错误
- **THEN** 系统不创建下载日志记录

---

### Requirement: Download Log Query API
系统 SHALL 提供 API 接口允许查询指定用户的下载日志。

接口规格：
- 端点：`GET /user/{user_id}/download-logs`
- 参数：
  - `user_id`（路径参数）：目标用户ID
  - `page`（查询参数，可选）：页码，默认为 1
  - `page_size`（查询参数，可选）：每页数量，默认为 10，最大 100
- 响应：包含日志列表和分页信息

#### Scenario: 查询用户下载日志成功
- **WHEN** superadmin 用户请求查询某用户的下载日志
- **THEN** 系统返回该用户的下载日志列表，按下载时间倒序排列，并包含分页信息

#### Scenario: 查询无下载记录的用户
- **WHEN** superadmin 用户请求查询一个没有下载记录的用户的日志
- **THEN** 系统返回空列表，total 为 0

---

### Requirement: Download Log Access Control
系统 SHALL 限制下载日志查询接口的访问权限。

只有 superadmin 角色的用户可以查询任意用户的下载日志。

#### Scenario: Superadmin 查询下载日志
- **WHEN** superadmin 角色的用户请求查询下载日志
- **THEN** 系统允许访问并返回日志数据

#### Scenario: 非 Superadmin 查询下载日志被拒绝
- **WHEN** admin 或 normal 角色的用户请求查询下载日志
- **THEN** 系统返回 403 Forbidden 错误

---

### Requirement: Download Log UI in Personnel Management
系统 SHALL 在人员管理页面的用户管理列表中提供下载日志查看功能。

用户管理表格的"操作"列 SHALL 包含"下载日志"按钮。

#### Scenario: 点击下载日志按钮显示弹窗
- **WHEN** superadmin 用户点击某用户记录的"下载日志"按钮
- **THEN** 系统显示一个弹窗，展示该用户的下载日志列表

#### Scenario: 下载日志弹窗展示内容
- **WHEN** 下载日志弹窗显示时
- **THEN** 弹窗标题显示"下载日志 - {用户ID}"
- **AND** 弹窗内包含表格，列包括：下载时间、合同名称
- **AND** 表格支持分页

#### Scenario: 用户无下载记录时的展示
- **WHEN** 被查询用户没有任何下载记录
- **THEN** 弹窗内显示"暂无下载记录"的空状态提示

