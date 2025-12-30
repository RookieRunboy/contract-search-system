# upload-queue Specification

## Purpose
TBD - created by archiving change add-upload-queue. Update Purpose after archive.
## Requirements
### Requirement: Upload Processing Concurrency Control
系统 SHALL 限制同时处理的上传任务数量，防止资源过载。

系统使用信号量（Semaphore）机制控制并发，默认最大并发数为 4。

#### Scenario: 并发限制生效
- **GIVEN** 系统配置最大并发处理数为 4
- **WHEN** 用户同时上传 10 个 PDF 文件
- **THEN** 系统立即接收所有 10 个文件并返回 queued 状态
- **AND** 最多只有 4 个文件同时进入解析处理流程
- **AND** 其余 6 个文件保持 pending 状态等待处理

#### Scenario: 队列按顺序处理
- **WHEN** 有多个 pending 状态的上传任务
- **THEN** 系统按照上传时间顺序（FIFO）依次处理

---

### Requirement: Configurable Concurrency Limit
系统 SHALL 支持通过环境变量配置最大并发处理数。

配置项：
- 环境变量名：`UPLOAD_MAX_CONCURRENT`
- 类型：正整数
- 默认值：4
- 有效范围：1 - 10

#### Scenario: 使用默认配置
- **WHEN** 未设置 `UPLOAD_MAX_CONCURRENT` 环境变量
- **THEN** 系统使用默认值 4 作为最大并发数

#### Scenario: 自定义并发数
- **GIVEN** 环境变量 `UPLOAD_MAX_CONCURRENT=5`
- **WHEN** 系统启动
- **THEN** 最大并发处理数设置为 5

#### Scenario: 无效配置回退默认值
- **GIVEN** 环境变量 `UPLOAD_MAX_CONCURRENT` 设置为非法值（如负数或非数字）
- **WHEN** 系统启动
- **THEN** 系统使用默认值 4 并打印警告日志

---

### Requirement: Upload Queue Status API
系统 SHALL 提供 API 接口查询当前上传队列状态。

接口规格：
- 端点：`GET /upload/queue-status`
- 权限：需要 admin 或 superadmin 角色
- 响应字段：
  - `pending_count`（整数）：待处理任务数量
  - `processing_count`（整数）：正在处理任务数量
  - `completed_today`（整数）：当日已完成数量
  - `failed_today`（整数）：当日失败数量
  - `max_concurrent`（整数）：最大并发配置值

#### Scenario: 查询队列状态成功
- **WHEN** admin 用户请求 `GET /upload/queue-status`
- **THEN** 系统返回当前队列状态信息
- **AND** 包含 pending_count、processing_count、max_concurrent 等字段

#### Scenario: 无权限用户访问被拒绝
- **WHEN** normal 角色用户请求 `GET /upload/queue-status`
- **THEN** 系统返回 403 Forbidden 错误

---

### Requirement: Upload Queue Status Display
系统前端 SHALL 在上传页面展示队列状态信息。

#### Scenario: 显示队列状态
- **WHEN** 用户访问上传页面且有任务在队列中
- **THEN** 页面显示当前队列状态
- **AND** 包含待处理数量和正在处理数量

#### Scenario: 上传后显示排队提示
- **WHEN** 用户成功上传文件且任务进入队列（非立即处理）
- **THEN** 系统显示提示信息："文件已加入处理队列，将按顺序处理"

#### Scenario: 队列为空时不显示
- **WHEN** 没有待处理或正在处理的任务
- **THEN** 不显示队列状态区域或显示"当前无任务排队"

---

### Requirement: Upload Speed Not Affected
上传接口 SHALL 不受并发处理限制的影响，始终快速响应。

#### Scenario: 高并发上传快速返回
- **GIVEN** 当前已有 10 个任务在队列中等待处理
- **WHEN** 用户上传新的 PDF 文件
- **THEN** 系统在 2 秒内返回 queued 状态响应
- **AND** 文件保存成功，任务加入队列

#### Scenario: 文件保存与解析解耦
- **WHEN** 用户上传 PDF 文件
- **THEN** 文件立即保存到 `uploaded_contracts/` 目录
- **AND** 创建 pending 状态的上传记录
- **AND** 解析任务异步执行，不阻塞响应

---

### Requirement: Memory Protection
系统 SHALL 在可用内存不足时暂停启动新的处理任务，防止 OOM 崩溃。

配置项：
- 环境变量名：`UPLOAD_MIN_MEMORY_MB`
- 类型：正整数（兆字节）
- 默认值：512（0.5GB）

#### Scenario: 内存充足时正常处理
- **GIVEN** 系统可用内存大于 `UPLOAD_MIN_MEMORY_MB`
- **WHEN** 有 pending 状态的任务等待处理
- **THEN** 系统立即开始处理下一个任务

#### Scenario: 内存不足时暂停处理
- **GIVEN** 系统可用内存低于 `UPLOAD_MIN_MEMORY_MB`
- **WHEN** 有 pending 状态的任务等待处理
- **THEN** 系统暂停启动新任务，每 5 秒检查一次内存状态
- **AND** 日志记录内存不足的等待情况
- **AND** 最多等待 5 分钟，超时后标记任务失败

#### Scenario: 内存恢复后继续处理
- **GIVEN** 系统因内存不足暂停处理
- **WHEN** 可用内存恢复到阈值以上
- **THEN** 系统自动恢复处理队列中的任务

---

### Requirement: Memory Leak Prevention
系统 SHALL 在处理完成后及时释放内存资源，防止内存泄漏。

#### Scenario: 释放 PIL Image 对象
- **WHEN** 每页 PDF 图片处理完成后
- **THEN** 系统调用 `image.close()` 释放 PIL Image 对象
- **AND** 清理图片列表引用

#### Scenario: 任务完成后垃圾回收
- **WHEN** 一个 PDF 文件处理完成
- **THEN** 系统调用 `gc.collect()` 强制垃圾回收
- **AND** 内存使用量应回落到合理水平

#### Scenario: 待机内存稳定
- **GIVEN** 系统已处理过多个 PDF 文件
- **WHEN** 所有任务处理完成且无新任务
- **THEN** Python 进程内存占用应稳定在 500MB 以下（不含 Elasticsearch）

---

### Requirement: Memory Status in Queue API
队列状态 API SHALL 包含内存使用信息。

扩展 `GET /upload/queue-status` 响应字段：
- `memory_total_mb`（整数）：系统总内存
- `memory_available_mb`（整数）：当前可用内存
- `memory_percent_used`（浮点）：内存使用百分比
- `memory_is_low`（布尔）：是否低于阈值

#### Scenario: 查询包含内存信息
- **WHEN** admin 用户请求 `GET /upload/queue-status`
- **THEN** 响应包含 memory_available_mb、memory_percent_used、memory_is_low 字段

#### Scenario: 前端显示内存警告
- **WHEN** memory_is_low 为 true
- **THEN** 前端显示内存不足警告提示

